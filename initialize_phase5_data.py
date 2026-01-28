"""
Initialize Phase 5 Data
Run this script to populate player stats and ELO ratings for the current season.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.analytics import update_player_stats, initialize_team_ratings
import config

def main():
    season = config.CURRENT_SEASON
    
    print(f"🚀 Initializing Phase 5 data for {season} season...")
    print()
    
    # Update player stats
    print("📊 Step 1: Updating player statistics...")
    try:
        result = update_player_stats(season)
        print(f"   ✅ Updated {result['players_updated']} players")
        print(f"   ✅ Added {result['new_players']} new players")
        if result['errors'] > 0:
            print(f"   ⚠️  {result['errors']} errors encountered")
    except Exception as e:
        print(f"   ❌ Error updating player stats: {e}")
    
    print()
    
    # Initialize ELO ratings
    print("⚡ Step 2: Initializing team ELO ratings...")
    try:
        initialize_team_ratings(season, week=1)
        print(f"   ✅ Initialized ELO ratings for all 32 teams")
    except Exception as e:
        print(f"   ⚠️  ELO initialization: {e}")
    
    print()
    print("🎉 Phase 5 data initialization complete!")
    print()
    print("Now you can:")
    print("  • View player performance in 🌟 Player Performance tab")
    print("  • Check defense matchups in 🛡️ Defense Matchups tab")
    print("  • See power rankings in ⚡ Power Rankings tab")
    print("  • Track ROI trends in 💰 ROI & Profitability tab")

if __name__ == "__main__":
    main()
