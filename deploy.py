"""
Quick deployment script for Railway
Commits changes and provides instructions for slash command setup
"""

import subprocess
import sys

def run_command(command, description):
    """Run a shell command and print the result"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    print("🚀 CodeVerse Bot - Quick Deploy & Slash Command Setup")
    print("=" * 55)
    
    # Check git status
    print("\n📋 Checking current changes...")
    subprocess.run("git status", shell=True)
    
    # Stage changes
    if not run_command("git add .", "Staging all changes"):
        return False
    
    # Commit changes
    commit_message = "Add slash command support and fix deployment"
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        print("ℹ️  No new changes to commit (this is normal)")
    
    # Push to GitHub
    if not run_command("git push origin master", "Pushing to GitHub"):
        return False
    
    print("\n" + "=" * 55)
    print("🎉 DEPLOYMENT COMPLETE!")
    print("=" * 55)
    
    print("\n📝 NEXT STEPS TO ENABLE SLASH COMMANDS:")
    print("\n1. 🔑 Update your Discord token in Railway:")
    print("   - Go to your Railway project dashboard")
    print("   - Click 'Variables' tab")
    print("   - Edit DISCORD_TOKEN variable")
    print("   - Paste your actual bot token")
    
    print("\n2. 🔄 Redeploy on Railway:")
    print("   - Railway will auto-deploy the new code")
    print("   - Wait for deployment to complete")
    
    print("\n3. ✨ Test slash commands:")
    print("   - Go to your Discord server")
    print("   - Type / and you should see:")
    print("     • /ping - Test bot connectivity")
    print("     • /info - Bot information")
    print("     • prefix changed to '?' (e.g., ?help)")
    
    print("\n4. 🔍 If slash commands still don't appear:")
    print("   - Wait 5-10 minutes for Discord to sync")
    print("   - Try leaving and rejoining your server")
    print("   - Check Railway logs for any errors")
    
    print("\n🆘 Need help? Check Railway logs:")
    print("   - Go to Railway dashboard")
    print("   - Click 'Logs' tab")
    print("   - Look for 'Synced X slash commands' message")
    
    print("\n🎯 Your bot should now support both:")
    print("   • Prefix commands: ?ping, ?quote, ?help")
    print("   • Slash commands: /ping, /quote, /info")

if __name__ == "__main__":
    main()
