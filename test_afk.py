"""
Test script for AFK system functionality
Tests database operations, command structure, and basic functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

import discord
from discord.ext import commands
from commands.afk import AFKSystem

async def test_afk_system():
    """Test the AFK system functionality"""
    print("🧪 Testing AFK System...")
    
    # Create a mock bot for testing
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='?', intents=intents)
    
    # Initialize AFK system
    afk_system = AFKSystem(bot)
    print("✅ AFK system initialized")
    
    # Test database initialization
    await afk_system.init_database()
    print("✅ Database initialized")
    
    # Test setting AFK status
    test_user_id = 123456789
    test_guild_id = 987654321
    test_reason = "Going to grab some coffee ☕"
    
    await afk_system.set_afk(test_user_id, test_guild_id, test_reason)
    print("✅ AFK status set successfully")
    
    # Test checking AFK status
    is_afk = afk_system.is_afk(test_user_id)
    assert is_afk == True, "User should be AFK"
    print("✅ AFK status check works")
    
    # Test getting AFK info
    afk_info = afk_system.get_afk_info(test_user_id)
    assert afk_info is not None, "AFK info should exist"
    assert afk_info['reason'] == test_reason, "Reason should match"
    assert afk_info['guild_id'] == test_guild_id, "Guild ID should match"
    print("✅ AFK info retrieval works")
    
    # Test incrementing mention count
    await afk_system.increment_mention_count(test_user_id)
    updated_info = afk_system.get_afk_info(test_user_id)
    assert updated_info is not None, "Updated info should exist"
    assert updated_info['mention_count'] == 1, "Mention count should be 1"
    print("✅ Mention count increment works")
    
    # Test duration formatting
    duration = afk_system.format_afk_duration(afk_info['set_time'])
    assert isinstance(duration, str), "Duration should be a string"
    print(f"✅ Duration formatting works: {duration}")
    
    # Test removing AFK status
    await afk_system.remove_afk(test_user_id)
    is_afk_after_removal = afk_system.is_afk(test_user_id)
    assert is_afk_after_removal == False, "User should not be AFK after removal"
    print("✅ AFK removal works")
    
    # Test cache loading
    await afk_system.set_afk(test_user_id, test_guild_id, "Testing cache")
    await afk_system.load_afk_cache()
    cached_info = afk_system.get_afk_info(test_user_id)
    assert cached_info is not None, "Cache should contain AFK info"
    print("✅ Cache loading works")
    
    # Clean up test data
    await afk_system.remove_afk(test_user_id)
    
    print("🎉 All AFK system tests passed!")
    
async def test_command_structure():
    """Test that all commands are properly structured"""
    print("\n🧪 Testing Command Structure...")
    
    # Create a mock bot
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='?', intents=intents)
    
    # Add the AFK cog
    afk_system = AFKSystem(bot)
    await bot.add_cog(afk_system)
    
    # Check that commands are registered
    afk_command = bot.get_command('afk')
    assert afk_command is not None, "AFK command should be registered"
    print("✅ AFK command registered")
    
    unafk_command = bot.get_command('unafk')
    assert unafk_command is not None, "UNAFK command should be registered"
    print("✅ UNAFK command registered")
    
    afklist_command = bot.get_command('afklist')
    assert afklist_command is not None, "AFKLIST command should be registered"
    print("✅ AFKLIST command registered")
    
    # Check that they're hybrid commands (have both slash and text versions)
    assert hasattr(afk_command, 'app_command'), "AFK should be a hybrid command"
    assert hasattr(unafk_command, 'app_command'), "UNAFK should be a hybrid command"
    assert hasattr(afklist_command, 'app_command'), "AFKLIST should be a hybrid command"
    print("✅ All commands are hybrid commands")
    
    # Check aliases
    back_command = bot.get_command('back')
    return_command = bot.get_command('return')
    assert back_command is not None, "BACK alias should work"
    assert return_command is not None, "RETURN alias should work"
    print("✅ Command aliases work")
    
    print("🎉 All command structure tests passed!")

async def main():
    """Run all tests"""
    print("🚀 Starting AFK System Tests...\n")
    
    try:
        await test_afk_system()
        await test_command_structure()
        print("\n✅ All tests completed successfully!")
        print("\n📝 AFK System Features:")
        print("   • Set AFK status with custom reasons")
        print("   • Automatic responses when AFK users are mentioned")
        print("   • Auto-return when user sends a message")
        print("   • Duration tracking and mention counters")
        print("   • Server-specific AFK status")
        print("   • Persistent SQLite database storage")
        print("   • Hybrid command support (?command and /command)")
        print("   • Comprehensive error handling")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)