def get_trophy_category(trophies):
    """Get trophy category for a player"""
    if trophies < 5000:
        return 'beginners'
    elif trophies < 15000:
        return 'intermediate'
    elif trophies < 30000:
        return 'advanced'
    elif trophies < 50000:
        return 'expert'
    elif trophies < 70000:
        return 'master'
    elif trophies < 90000:
        return 'legendary'
    else:
        return 'mythical'

def categories_full():
    """Check if all categories have enough players"""
    for category, players in players_by_category.items():
        if len(players) < MAX_PLAYERS_PER_CATEGORY:
            return False
    return True

def get_needed_categories():
    """Get list of categories that still need players"""
    needed = []
    for category, players in players_by_category.items():
        if len(players) < MAX_PLAYERS_PER_CATEGORY:
            needed.append(category)
    return needed#!/usr/bin/env python3
"""
Player Tag Collector - Snowball Strategy
Collect as many player tags as possible using club crawling
Output: Simple list of player tags + trophy counts
"""

import requests
import time
import csv
from datetime import datetime

# Configuration
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjcyOGRhZjZjLWY0ZmQtNDlhMS05OTdiLTdmMDM1MzRlZmY2NiIsImlhdCI6MTc0OTUzMDg3OSwic3ViIjoiZGV2ZWxvcGVyLzBlNzNiYWEwLTU4OTUtYjhjNi00ODEzLWY3OTFkZDk0OTgxZSIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMjMuOTcuNjIuMTQ2Il0sInR5cGUiOiJjbGllbnQifV19._gQxv_yjH88W3HpeC2dpPV3v_c2GeIvrSMD0BRhmYnJRQsV_kuEMlwiCAknYx4GsoZQTRzBaQ_sOJszuP9EQtA"
API_BASE = "https://api.brawlstars.com/v1"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

# SEED PLAYERS - Add ANY known player tags here
SEED_PLAYERS = [
    "#2G09L9QRC",     # Replace with real tags
    "#8Y8CC02J",      
    "#9PYLCCGR",
    # Add more seed players here - the more the better!
]

# Settings
MAX_CLUBS_TO_EXPLORE = 50      # How many clubs to explore (increased for more players)
MAX_PLAYERS_PER_CATEGORY = 150 # Target players per trophy range

# Storage
collected_players = {}  # {tag: {name, trophies, club_name}}
players_by_category = {
    'beginners': {},      # 0-5K
    'intermediate': {},   # 5K-15K  
    'advanced': {},       # 15K-30K
    'expert': {},         # 30K-50K
    'master': {},         # 50K-70K
    'legendary': {},      # 70K-90K
    'mythical': {}        # 90K+
}
processed_clubs = set()

def get_player_basic_info(player_tag):
    """Get basic player info (name, trophies, club)"""
    try:
        encoded_tag = player_tag.replace('#', '%23')
        response = requests.get(f"{API_BASE}/players/{encoded_tag}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'tag': data.get('tag', player_tag),
                'name': data.get('name', 'Unknown'),
                'trophies': data.get('trophies', 0),
                'club_tag': data.get('club', {}).get('tag'),
                'club_name': data.get('club', {}).get('name', 'No Club')
            }
        elif response.status_code == 404:
            print(f"    Player {player_tag} not found")
        else:
            print(f"    Error {response.status_code} for player {player_tag}")
            
    except Exception as e:
        print(f"    Exception getting player {player_tag}: {e}")
    
    return None

def get_club_members(club_tag):
    """Get all members from a club"""
    try:
        encoded_tag = club_tag.replace('#', '%23')
        response = requests.get(f"{API_BASE}/clubs/{encoded_tag}", headers=headers)
        
        if response.status_code == 200:
            club_data = response.json()
            club_name = club_data.get('name', 'Unknown Club')
            members = club_data.get('members', [])
            return club_name, members
        else:
            print(f"    Error {response.status_code} getting club {club_tag}")
            
    except Exception as e:
        print(f"    Exception getting club {club_tag}: {e}")
    
    return None, []

def snowball_collect_tags():
    """Use snowball strategy to collect as many player tags as possible"""
    print("🔥 Starting Snowball Player Tag Collection")
    print(f"🎯 Target: {MAX_PLAYERS_TO_COLLECT} players from {MAX_CLUBS_TO_EXPLORE} clubs")
    print("=" * 60)
    
    clubs_to_explore = set()
    
    # Phase 1: Get clubs from seed players
    print(f"🌱 Phase 1: Getting clubs from {len(SEED_PLAYERS)} seed players...")
    
    for i, seed_tag in enumerate(SEED_PLAYERS, 1):
        print(f"  {i}. Getting info for seed player {seed_tag}...")
        
        player_info = get_player_basic_info(seed_tag)
        if player_info:
            # Add seed player to collection
            collected_players[player_info['tag']] = player_info
            print(f"     ✅ {player_info['name']} ({player_info['trophies']} trophies)")
            
            # Add their club to exploration list
            if player_info['club_tag']:
                clubs_to_explore.add(player_info['club_tag'])
                print(f"     🏠 Added club: {player_info['club_name']}")
        else:
            print(f"     ❌ Could not get info for {seed_tag}")
        
        time.sleep(0.3)  # Rate limiting
    
    print(f"\n✅ Phase 1 Complete: {len(collected_players)} players, {len(clubs_to_explore)} clubs to explore")
    
    # Phase 2: Explore clubs and collect members
    print(f"\n🏠 Phase 2: Exploring clubs for members...")
    
    clubs_explored = 0
    clubs_list = list(clubs_to_explore)
    
    for club_tag in clubs_list[:MAX_CLUBS_TO_EXPLORE]:
        if len(collected_players) >= MAX_PLAYERS_TO_COLLECT:
            print(f"✅ Reached target of {MAX_PLAYERS_TO_COLLECT} players!")
            break
            
        if club_tag in processed_clubs:
            continue
            
        clubs_explored += 1
        print(f"\n  🏠 Club {clubs_explored}/{min(len(clubs_list), MAX_CLUBS_TO_EXPLORE)}: {club_tag}")
        
        club_name, members = get_club_members(club_tag)
        if not members:
            print(f"     ❌ No members found")
            continue
            
        processed_clubs.add(club_tag)
        print(f"     📊 {club_name} has {len(members)} members")
        
        # Collect member info
        new_players_this_club = 0
        trophy_ranges = {'0-5K': 0, '5K-15K': 0, '15K-30K': 0, '30K-50K': 0, '50K-70K': 0, '70K-90K': 0, '90K+': 0}
        
        for member in members:
            member_tag = member.get('tag', '')
            member_name = member.get('name', 'Unknown')
            member_trophies = member.get('trophies', 0)
            
            # Skip if already collected
            if member_tag in collected_players:
                continue
            
            # Add to collection
            collected_players[member_tag] = {
                'tag': member_tag,
                'name': member_name,
                'trophies': member_trophies,
                'club_tag': club_tag,
                'club_name': club_name
            }
            
            new_players_this_club += 1
            
            # Count trophy ranges for diversity tracking
            if member_trophies < 5000:
                trophy_ranges['0-5K'] += 1
            elif member_trophies < 15000:
                trophy_ranges['5K-15K'] += 1
            elif member_trophies < 30000:
                trophy_ranges['15K-30K'] += 1
            else:
                trophy_ranges['30K+'] += 1
        
        print(f"     ✅ Added {new_players_this_club} new players")
        print(f"     📈 Trophy diversity: {trophy_ranges}")
        print(f"     📊 Total collected: {len(collected_players)} players")
        
        time.sleep(0.5)  # Rate limiting between clubs
    
    print(f"\n🎉 Collection Complete!")
    print(f"📊 Total players collected: {len(collected_players)}")
    print(f"🏠 Clubs explored: {clubs_explored}")

def analyze_collection():
    """Analyze the collected players"""
    print(f"\n📊 COLLECTION ANALYSIS")
    print("=" * 50)
    
    if not collected_players:
        print("No players collected!")
        return
    
    # Show progress for each category
    print(f"Players per category (Target: {MAX_PLAYERS_PER_CATEGORY} each):")
    total_collected = 0
    
    for category, players in players_by_category.items():
        count = len(players)
        total_collected += count
        percentage = (count / MAX_PLAYERS_PER_CATEGORY * 100) if count > 0 else 0
        status = "✅" if count >= MAX_PLAYERS_PER_CATEGORY else "📈"
        
        if count > 0:
            trophies_list = [p['trophies'] for p in players.values()]
            avg_trophies = sum(trophies_list) / len(trophies_list)
            min_trophies = min(trophies_list)
            max_trophies = max(trophies_list)
            print(f"  {status} {category}: {count}/{MAX_PLAYERS_PER_CATEGORY} ({percentage:.1f}%) - Avg: {avg_trophies:,.0f} (Range: {min_trophies:,}-{max_trophies:,})")
        else:
            print(f"  ❌ {category}: {count}/{MAX_PLAYERS_PER_CATEGORY} (0%)")
    
    print(f"\nTotal Players Collected: {total_collected:,}")
    
    # Overall trophy stats
    all_trophies = [p['trophies'] for p in collected_players.values()]
    if all_trophies:
        all_trophies.sort()
        print(f"\nOverall Trophy Statistics:")
        print(f"  Min: {min(all_trophies):,}")
        print(f"  Max: {max(all_trophies):,}")
        print(f"  Average: {sum(all_trophies) / len(all_trophies):,.0f}")
        print(f"  Median: {all_trophies[len(all_trophies)//2]:,}")

def save_to_csv():
    """Save collected player tags to CSV"""
    filename = f"player_tags_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['player_tag', 'player_name', 'trophies', 'club_name', 'trophy_category'])
        
        # Write players from each category
        for category, players in players_by_category.items():
            for player_info in players.values():
                writer.writerow([
                    player_info['tag'],
                    player_info['name'],
                    player_info['trophies'],
                    player_info['club_name'],
                    category
                ])
    
    total_saved = sum(len(players) for players in players_by_category.values())
    print(f"\n💾 Saved {total_saved} player tags to: {filename}")
    
    # Show breakdown by category
    print("📊 Breakdown by category:")
    for category, players in players_by_category.items():
        print(f"  {category}: {len(players)} players")
    
    return filename

def main():
    """Main collection pipeline"""
    print("🎯 Brawl Stars Player Tag Collector")
    print("=" * 50)
    
    if SEED_PLAYERS == ["#2G09L9QRC", "#8Y8CC02J", "#9PYLCCGR"]:
        print("⚠️  Please add real player tags to SEED_PLAYERS!")
        print("   You need at least 1-2 real player tags to start the snowball")
        return
    
    # Collect player tags using snowball strategy
    snowball_collect_tags()
    
    # Analyze what we collected
    analyze_collection()
    
    # Save to CSV
    if collected_players:
        filename = save_to_csv()
        print(f"\n🎉 SUCCESS!")
        print(f"📁 Player tags saved to: {filename}")
        print(f"💡 You can now use these tags for detailed data extraction")
    else:
        print("\n❌ No players collected - check your seed player tags")

if __name__ == "__main__":
    main()
