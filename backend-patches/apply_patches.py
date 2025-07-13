#!/usr/bin/env python3
"""
Script para aplicar patches no código original do SUNA
para funcionar em modo local
"""

import os
import shutil
import sys
from pathlib import Path


def apply_patches(suna_backend_dir: str, patches_dir: str):
    """Apply patches to SUNA backend code"""
    
    suna_path = Path(suna_backend_dir)
    patches_path = Path(patches_dir)
    
    if not suna_path.exists():
        print(f"❌ Diretório backend não encontrado: {suna_backend_dir}")
        return False
    
    if not patches_path.exists():
        print(f"❌ Diretório de patches não encontrado: {patches_dir}")
        return False
    
    print(f"🔧 Aplicando patches no diretório: {suna_backend_dir}")
    
    # 1. Copy new files
    print("📁 Copiando novos arquivos...")
    
    # Copy config.py to utils/
    config_src = patches_path / "config.py"
    config_dst = suna_path / "utils" / "config.py"
    if config_src.exists():
        shutil.copy2(config_src, config_dst)
        print(f"   ✓ {config_dst}")
    
    # Copy local services
    services_dir = suna_path / "services"
    services_dir.mkdir(exist_ok=True)
    
    local_llm_src = patches_path / "local_llm_service.py"
    local_llm_dst = services_dir / "local_llm_service.py"
    if local_llm_src.exists():
        shutil.copy2(local_llm_src, local_llm_dst)
        print(f"   ✓ {local_llm_dst}")
    
    local_db_src = patches_path / "local_database.py"
    local_db_dst = services_dir / "local_database.py"
    if local_db_src.exists():
        shutil.copy2(local_db_src, local_db_dst)
        print(f"   ✓ {local_db_dst}")
    
    local_auth_src = patches_path / "local_auth.py"
    local_auth_dst = services_dir / "local_auth.py"
    if local_auth_src.exists():
        shutil.copy2(local_auth_src, local_auth_dst)
        print(f"   ✓ {local_auth_dst}")
    
    # Copy local tools
    tools_dir = suna_path / "agent" / "tools"
    local_tools_src = patches_path / "local_tools.py"
    local_tools_dst = tools_dir / "local_tools.py"
    if local_tools_src.exists():
        shutil.copy2(local_tools_src, local_tools_dst)
        print(f"   ✓ {local_tools_dst}")
    
    # Copy test script
    test_src = patches_path / "test_llama_server.py"
    test_dst = suna_path / "test_llama_server.py"
    if test_src.exists():
        shutil.copy2(test_src, test_dst)
        os.chmod(test_dst, 0o755)
        print(f"   ✓ {test_dst}")
    
    # 2. Modify existing files
    print("🔄 Modificando arquivos existentes...")
    
    # Modify api.py to add local mode support
    api_file = suna_path / "api.py"
    if api_file.exists():
        modify_api_file(api_file)
        print(f"   ✓ {api_file}")
    
    # Modify agent/run.py
    run_file = suna_path / "agent" / "run.py"
    if run_file.exists():
        modify_run_file(run_file)
        print(f"   ✓ {run_file}")
    
    # Modify services/llm.py if exists
    llm_file = suna_path / "services" / "llm.py"
    if llm_file.exists():
        modify_llm_file(llm_file)
        print(f"   ✓ {llm_file}")
    
    # Modify utils/auth_utils.py if exists
    auth_utils_file = suna_path / "utils" / "auth_utils.py"
    if auth_utils_file.exists():
        modify_auth_utils_file(auth_utils_file)
        print(f"   ✓ {auth_utils_file}")
    
    # Modify agentpress/thread_manager.py if exists
    thread_manager_file = suna_path / "agentpress" / "thread_manager.py"
    if thread_manager_file.exists():
        modify_thread_manager_file(thread_manager_file)
        print(f"   ✓ {thread_manager_file}")
    
    print("✅ Patches aplicados com sucesso!")
    return True


def modify_api_file(api_file: Path):
    """Modify api.py to support local mode"""
    
    content = api_file.read_text()
    
    # Add imports for local mode
    if "from utils.config import config, EnvMode" not in content:
        content = content.replace(
            "from utils.logger import logger",
            "from utils.logger import logger\nfrom utils.config import config, EnvMode"
        )
    
    # Add local mode check in streaming endpoint
    if "# In LOCAL mode, use default values" not in content:
        streaming_func = """async def stream_agent_run(
    thread_id: str = Form(...),
    project_id: str = Form(...),
):"""
        
        if streaming_func in content:
            replacement = """async def stream_agent_run(
    thread_id: str = Form(...),
    project_id: str = Form(...),
):
    # In LOCAL mode, use default values
    if config.ENV_MODE == EnvMode.LOCAL:
        if not thread_id or thread_id == "undefined":
            thread_id = f"local-thread-{uuid.uuid4()}"
        if not project_id or project_id == "undefined":
            project_id = config.LOCAL_PROJECT_ID"""
            
            content = content.replace(streaming_func, replacement)
    
    api_file.write_text(content)


def modify_run_file(run_file: Path):
    """Modify agent/run.py to support local mode"""
    
    content = run_file.read_text()
    
    # Add local imports
    if "from services.local_llm_service import make_llm_api_call" not in content:
        content = content.replace(
            "from utils.config import config",
            "from utils.config import config, is_local_mode\nfrom services.local_llm_service import make_llm_api_call as local_make_llm_api_call"
        )
    
    # Replace default model
    content = content.replace(
        'model_name: str = "gpt-4"',
        'model_name: str = "local-mistral"'
    )
    
    run_file.write_text(content)


def modify_llm_file(llm_file: Path):
    """Modify services/llm.py to support local mode"""
    
    content = llm_file.read_text()
    
    # Add local mode import and check
    if "from utils.config import config, is_local_mode" not in content:
        content = content.replace(
            "import openai",
            "import openai\nfrom utils.config import config, is_local_mode\nfrom .local_llm_service import make_llm_api_call as local_make_llm_api_call"
        )
    
    # Modify make_llm_api_call function
    if "if is_local_mode():" not in content:
        func_start = "async def make_llm_api_call("
        if func_start in content:
            # Find the function and add local mode check at the beginning
            lines = content.split('\\n')
            new_lines = []
            in_function = False
            indent_added = False
            
            for line in lines:
                if func_start in line:
                    in_function = True
                    new_lines.append(line)
                elif in_function and line.strip() and not line.startswith(' ') and not line.startswith('\\t'):
                    in_function = False
                    new_lines.append(line)
                elif in_function and not indent_added and line.strip() and (line.startswith('    ') or line.startswith('\\t')):
                    # Add local mode check
                    new_lines.append("    if is_local_mode():")
                    new_lines.append("        return await local_make_llm_api_call(model, messages, temperature, max_tokens, stream)")
                    new_lines.append("")
                    new_lines.append(line)
                    indent_added = True
                else:
                    new_lines.append(line)
            
            content = '\\n'.join(new_lines)
    
    llm_file.write_text(content)


def modify_auth_utils_file(auth_utils_file: Path):
    """Modify utils/auth_utils.py to support local mode"""
    
    content = auth_utils_file.read_text()
    
    # Add local mode import
    if "from utils.config import config, is_local_mode" not in content:
        content = content.replace(
            "from utils.logger import logger",
            "from utils.logger import logger\nfrom utils.config import config, is_local_mode"
        )
    
    # Modify verify_user_token function
    if "if is_local_mode():" not in content:
        func_start = "async def verify_user_token("
        if func_start in content:
            content = content.replace(
                func_start,
                f"""{func_start}
    if is_local_mode():
        logger.info("LOCAL mode: Bypassing authentication")
        return config.LOCAL_USER_ID
    
    # Original authentication logic follows"""
            )
    
    auth_utils_file.write_text(content)


def modify_thread_manager_file(thread_manager_file: Path):
    """Modify agentpress/thread_manager.py to support local mode"""
    
    content = thread_manager_file.read_text()
    
    # Add imports
    if "from utils.config import config, is_local_mode" not in content:
        content = content.replace(
            "from utils.logger import logger",
            "from utils.logger import logger\nfrom utils.config import config, is_local_mode\nfrom services.local_database import local_db"
        )
    
    # Modify add_message method
    if "if is_local_mode():" not in content:
        add_message_start = "async def add_message("
        if add_message_start in content:
            # Find the method and add local mode check
            lines = content.split('\\n')
            new_lines = []
            in_method = False
            indent_added = False
            
            for line in lines:
                if add_message_start in line:
                    in_method = True
                    new_lines.append(line)
                elif in_method and line.strip() and not line.startswith(' ') and not line.startswith('\\t') and 'def ' in line:
                    in_method = False
                    new_lines.append(line)
                elif in_method and not indent_added and 'logger.debug' in line:
                    new_lines.append(line)
                    new_lines.append("")
                    new_lines.append("        # In local mode, use local database")
                    new_lines.append("        if is_local_mode():")
                    new_lines.append("            return await local_db.add_message(thread_id, type, content, is_llm_message, metadata)")
                    new_lines.append("")
                    indent_added = True
                else:
                    new_lines.append(line)
            
            content = '\\n'.join(new_lines)
    
    thread_manager_file.write_text(content)


def main():
    """Main function"""
    
    if len(sys.argv) != 3:
        print("Uso: python apply_patches.py <suna_backend_dir> <patches_dir>")
        print("Exemplo: python apply_patches.py /home/user/suna-local/backend ./backend-patches")
        sys.exit(1)
    
    suna_backend_dir = sys.argv[1]
    patches_dir = sys.argv[2]
    
    success = apply_patches(suna_backend_dir, patches_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

