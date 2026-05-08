import subprocess
import os
from database import get_console_paths, get_rom_file


def launch_game(console_id, rom_id):
    """
    Launch emulator with selected ROM.
    Return: (success: bool, message: str)
    """

    console_data = get_console_paths(console_id)
    rom_data = get_rom_file(rom_id)

    # ❌ ไม่มีข้อมูล
    if not console_data or not rom_data:
        return False, "Missing console or ROM data."

    emu_path, rom_folder = console_data
    file_name = rom_data[0]

    if not emu_path:
        return False, "Emulator path not set."

    full_rom_path = os.path.join(rom_folder, file_name)

    # ❌ เช็คไฟล์
    if not os.path.exists(emu_path):
        return False, f"Emulator not found: {emu_path}"

    if not os.path.exists(full_rom_path):
        return False, f"ROM file not found: {full_rom_path}"

    try:
        subprocess.Popen([emu_path, full_rom_path])
        return True, "Game launched."
    except Exception as e:
        return False, str(e)