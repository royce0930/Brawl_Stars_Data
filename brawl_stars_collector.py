import requests
import pandas as pd
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrawlStarsAPICollector:
    def __init__(self, api_token: str, rate_limit_delay: float = 0.1):
        """
        Initialize the Brawl Stars API collector
        
        Args:
            api_token: Your Brawl Stars API token
            rate_limit_delay: Delay between API calls to respect rate limits
        """
        self.api_token = api_token
        self.base_url = "https://api.brawlstars.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json"
        }
        self.rate_limit_delay = rate_limit_delay
        
        # Data storage
        self.battles_data = []
        self.players_data = []
        self.player_brawler_data = []
        self.battle_players_data = []
        self.maps_data = []
        self.game_modes_data = []
        self.brawlers_data = []
        
        # Track processed data to avoid duplicates
        self.processed_battle_ids = set()
        self.processed_player_tags = set()
        
    def make_api_request(self, endpoint: str) -> Optional[Dict]:
        """Make a request to the Brawl Stars API with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            time.sleep(self.rate_limit_delay)  # Rate limiting
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Resource not found: {endpoint}")
                return None
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting 60 seconds...")
                time.sleep(60)
                return self.make_api_request(endpoint)  # Retry
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception during API request: {e}")
            return None
    
    def load_player_tags(self, csv_file_path: str) -> List[str]:
        """Load player tags from CSV file"""
        try:
            df = pd.read_csv(csv_file_path)
            tags = df['player_tag'].tolist()
            logger.info(f"Loaded {len(tags)} player tags from {csv_file_path}")
            return tags
        except Exception as e:
            logger.error(f"Error loading player tags: {e}")
            return []
    
    def fetch_brawlers(self):
        """Fetch all brawlers data"""
        logger.info("Fetching brawlers data...")
        data = self.make_api_request("/brawlers")
        
        if data and 'items' in data:
            current_time = datetime.now()
            for brawler in data['items']:
                self.brawlers_data.append({
                    'id': brawler['id'],
                    'name': brawler['name'],
                    'rarity': brawler.get('rarity', {}).get('name', ''),
                    'class': brawler.get('class', {}).get('name', ''),
                    'description': brawler.get('description', ''),
                    'created_at': current_time,
                    'updated_at': current_time
                })
            logger.info(f"Fetched {len(self.brawlers_data)} brawlers")
    
    def fetch_player_data(self, player_tag: str):
        """Fetch player data and their brawlers"""
        if player_tag in self.processed_player_tags:
            return
            
        # Remove # if present and encode for URL
        clean_tag = player_tag.replace('#', '').replace(' ', '')
        endpoint = f"/players/%23{clean_tag}"
        
        logger.info(f"Fetching data for player: {player_tag}")
        data = self.make_api_request(endpoint)
        
        if not data:
            return
            
        current_time = datetime.now()
        
        # Extract player data
        player_data = {
            'tag': data['tag'],
            'name': data['name'],
            'trophies': data.get('trophies', 0),
            'highest_trophies': data.get('highestTrophies', 0),
            'exp_level': data.get('expLevel', 0),
            'victories_3v3': data.get('3vs3Victories', 0),
            'victories_solo': data.get('soloVictories', 0),
            'victories_duo': data.get('duoVictories', 0),
            'club_id': data.get('club', {}).get('tag', ''),
            'created_at': current_time,
            'updated_at': current_time
        }
        self.players_data.append(player_data)
        
        # Extract brawler data for this player
        if 'brawlers' in data:
            for brawler in data['brawlers']:
                brawler_data = {
                    'player_tag': data['tag'],
                    'brawler_id': brawler['id'],
                    'power_level': brawler.get('power', 0),
                    'trophies': brawler.get('trophies', 0),
                    'highest_trophies': brawler.get('highestTrophies', 0),
                    'rank': brawler.get('rank', 0),
                    'created_at': current_time,
                    'updated_at': current_time
                }
                self.player_brawler_data.append(brawler_data)
        
        self.processed_player_tags.add(player_tag)
    
    def fetch_player_battles(self, player_tag: str):
        """Fetch battle log for a player"""
        clean_tag = player_tag.replace('#', '').replace(' ', '')
        endpoint = f"/players/%23{clean_tag}/battlelog"
        
        logger.info(f"Fetching battles for player: {player_tag}")
        data = self.make_api_request(endpoint)
        
        if not data or 'items' not in data:
            return
            
        current_time = datetime.now()
        
        for battle in data['items']:
            battle_id = f"{battle['battleTime']}_{player_tag}"
            
            if battle_id in self.processed_battle_ids:
                continue
                
            # Extract battle data
            battle_data = {
                'id': battle_id,
                'battle_time': battle['battleTime'],
                'mode_id': battle.get('battle', {}).get('mode', ''),
                'map_id': battle.get('battle', {}).get('map', ''),
                'type': battle.get('battle', {}).get('type', ''),
                'result': battle.get('battle', {}).get('result', ''),
                'duration': battle.get('battle', {}).get('duration', 0),
                'trophy_change': battle.get('battle', {}).get('trophyChange', 0),
                'star_player_tag': battle.get('battle', {}).get('starPlayer', {}).get('tag', '')
            }
            self.battles_data.append(battle_data)
            
            # Extract battle players data
            teams = battle.get('battle', {}).get('teams', [])
            if teams:
                for team_idx, team in enumerate(teams):
                    for player in team:
                        battle_player_data = {
                            'battle_id': battle_id,
                            'player_tag': player.get('tag', ''),
                            'team': team_idx,
                            'brawler_id': player.get('brawler', {}).get('id', ''),
                            'brawler_power': player.get('brawler', {}).get('power', 0),
                            'brawler_trophies': player.get('brawler', {}).get('trophies', 0),
                            'created_at': current_time,
                            'id': len(self.battle_players_data) + 1
                        }
                        self.battle_players_data.append(battle_player_data)
            
            # Handle maps data
            map_name = battle.get('event', {}).get('map', '')
            if map_name:
                map_data = {
                    'id': len(self.maps_data) + 1,
                    'name': map_name,
                    'mode_id': battle.get('event', {}).get('mode', ''),
                    'environment': '',  # Not available in API
                    'created_at': current_time,
                    'updated_at': current_time
                }
                # Check if map already exists
                if not any(m['name'] == map_name for m in self.maps_data):
                    self.maps_data.append(map_data)
            
            # Handle game modes data
            mode_name = battle.get('event', {}).get('mode', '')
            if mode_name:
                mode_data = {
                    'id': len(self.game_modes_data) + 1,
                    'name': mode_name,
                    'color': '',  # Not available in API
                    'created_at': current_time,
                    'updated_at': current_time
                }
                # Check if mode already exists
                if not any(m['name'] == mode_name for m in self.game_modes_data):
                    self.game_modes_data.append(mode_data)
            
            self.processed_battle_ids.add(battle_id)
    
    def save_to_csv(self, output_dir: str = "./brawl_stars_data"):
        """Save all collected data to CSV files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Define data mappings
        data_mappings = {
            'battles.csv': self.battles_data,
            'players.csv': self.players_data,
            'player_brawler.csv': self.player_brawler_data,
            'battle_players.csv': self.battle_players_data,
            'maps.csv': self.maps_data,
            'game_modes.csv': self.game_modes_data,
            'brawlers.csv': self.brawlers_data
        }
        
        for filename, data in data_mappings.items():
            if data:
                df = pd.DataFrame(data)
                filepath = os.path.join(output_dir, filename)
                df.to_csv(filepath, index=False)
                logger.info(f"Saved {len(data)} records to {filepath}")
            else:
                logger.warning(f"No data to save for {filename}")
    
    def collect_all_data(self, player_tags_csv: str):
        """Main method to collect all data"""
        logger.info("Starting data collection...")
        
        # Load player tags
        player_tags = self.load_player_tags(player_tags_csv)
        if not player_tags:
            logger.error("No player tags loaded. Exiting.")
            return
        
        # Fetch brawlers data (only needs to be done once)
        self.fetch_brawlers()
        
        # Process each player
        total_players = len(player_tags)
        for i, player_tag in enumerate(player_tags, 1):
            logger.info(f"Processing player {i}/{total_players}: {player_tag}")
            
            # Fetch player data and brawlers
            self.fetch_player_data(player_tag)
            
            # Fetch player battles
            self.fetch_player_battles(player_tag)
            
            # Progress update every 10 players
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{total_players} players processed")
        
        logger.info("Data collection completed!")
        logger.info(f"Collected:")
        logger.info(f"  - {len(self.battles_data)} battles")
        logger.info(f"  - {len(self.players_data)} players")
        logger.info(f"  - {len(self.player_brawler_data)} player-brawler records")
        logger.info(f"  - {len(self.battle_players_data)} battle-player records")
        logger.info(f"  - {len(self.maps_data)} unique maps")
        logger.info(f"  - {len(self.game_modes_data)} unique game modes")
        logger.info(f"  - {len(self.brawlers_data)} brawlers")


# Example usage
def main():
    # Replace with your actual Brawl Stars API token
    API_TOKEN = input("Enter your Brawl Stars API token: ").strip()
    
    if not API_TOKEN:
        print("Error: API token is required!")
        return
    
    print("Starting Brawl Stars data collection...")
    print("This will process all 350 player tags and may take 30-60 minutes.")
    
    # Initialize collector
    collector = BrawlStarsAPICollector(API_TOKEN, rate_limit_delay=0.1)
    
    # Collect all data
    collector.collect_all_data("Brawler Stars Offical Tag  Sheet2.csv")
    
    # Save to CSV files
    collector.save_to_csv("./brawl_stars_data")
    
    print("\n" + "="*50)
    print("DATA COLLECTION COMPLETE!")
    print("="*50)
    print("Check the './brawl_stars_data' directory for your CSV files:")
    print("- battles.csv")
    print("- players.csv")
    print("- player_brawler.csv")
    print("- battle_players.csv")
    print("- maps.csv")
    print("- game_modes.csv")
    print("- brawlers.csv")

if __name__ == "__main__":
    main()
