#!/usr/bin/env python3
"""Test script to validate desktop notifications are working.

This script tests if desktop notifications are properly configured.
On macOS 10.14+, this requires a SIGNED Python executable.

Usage:
    python scripts/test_notifications.py

If no notification appears but the script says "Success", you likely need
to sign your Python executable:

    codesign -s - $(which python3)

Or install Python from python.org instead of Homebrew.
"""

import asyncio
import platform
import subprocess
import sys


async def main():
    import os

    print("=" * 60)
    print("Mosaic Notification Test")
    print("=" * 60)
    print()

    # Check platform
    system = platform.system()
    print(f"Platform: {system}")
    print(f"Python executable: {sys.executable}")

    # Resolve symlinks to find actual executable
    real_python = os.path.realpath(sys.executable)
    if real_python != sys.executable:
        print(f"Real executable:   {real_python}")
    print()

    # Check if Python executable is signed (macOS only)
    if system == "Darwin":
        print("Checking code signature...")
        try:
            result = subprocess.run(
                ["codesign", "-dv", real_python],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print("✅ Python executable is signed")
                print(f"   {result.stderr.strip()}")
            else:
                print("❌ Python executable is NOT signed")
                print()
                print("CRITICAL: macOS 10.14+ requires signed executables for notifications")
                print("To fix, run:")
                print(f"    codesign -s - {real_python}")
                print()
                print("Or install Python from python.org instead of Homebrew")
        except FileNotFoundError:
            print("⚠️  Could not check signature (codesign not found)")
        print()

    # Test notification
    print("Sending test notification...")
    print("(Check your notification center for 'Test Notification')")
    print()

    try:
        from desktop_notifier import DesktopNotifier

        notifier = DesktopNotifier(app_name="Mosaic")

        # Check capabilities
        capabilities = await notifier.get_capabilities()
        print("Notification capabilities:")
        if isinstance(capabilities, (set, frozenset)):
            for capability in capabilities:
                print(f"  - {capability}")
        elif isinstance(capabilities, dict):
            for key, value in capabilities.items():
                print(f"  - {key}: {value}")
        else:
            print(f"  - {capabilities}")
        print()

        # Send test notification
        await notifier.send(
            title="Test Notification",
            message="If you see this, notifications are working! 🎉",
        )

        print("✅ Notification sent successfully")
        print()
        print("Did you see the notification?")
        print("  - YES: Notifications are working correctly! ✅")
        print("  - NO:  Check System Settings → Notifications")
        print()
        print("TROUBLESHOOTING:")
        print("If you didn't see a notification:")
        print("1. Open System Settings → Notifications")
        print("2. Look for 'Mosaic' in the list")
        print("3. Enable 'Allow Notifications'")
        print("4. Enable 'Alerts' (not just 'Banners')")
        print()
        print("If Mosaic isn't in the list:")
        print("  - The Python executable needs to request notification permission")
        print("  - Try running this script again - you should see a permission prompt")
        print("  - If still no prompt, the executable may need signing (see above)")
        print()
        print(f"To sign the executable, run:")
        print(f"    codesign -s - {real_python}")
        print()

    except Exception as e:
        print(f"❌ Failed to send notification: {e}")
        print()
        print("Error details:")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
