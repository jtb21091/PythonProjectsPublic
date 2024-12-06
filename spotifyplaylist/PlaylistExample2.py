import os
import time
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Spotify API credentials from environment variables
client_id = os.getenv("SPOTIFY_CLIENT_ID")         # Set this in your environment
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET") # Set this in your environment
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI",)  # Default redirect URI

if not client_id or not client_secret:
    raise ValueError("Spotify API credentials are not set. Please set them as environment variables.")

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope="playlist-modify-public",
    open_browser=True
))

# Function to fetch random EDM songs from different search queries
def get_random_popular_edm_songs(limit=10000):
    edm_tracks = []
    track_uris = []
    queries = ["genre:edm", "genre:electronic", "genre:house", "genre:techno"]  # Multiple queries to increase diversity
    tracks_per_query = min(limit // len(queries), 1000)  # Max 1000 per query due to Spotify API limit

    for query in queries:
        offset = 0
        while len(track_uris) < limit and offset < 1000:  # Stay within the 1000 offset limit
            results = sp.search(
                q=query, type="track", limit=50, offset=offset
            )
            if not results['tracks']['items']:
                break

            for item in results['tracks']['items']:
                track_name = item['name']
                artist_name = item['artists'][0]['name']
                track_uri = item['uri']

                edm_tracks.append(f"{len(track_uris) + 1}. {track_name} by {artist_name}")
                track_uris.append(track_uri)

                # Stop if we've reached the limit
                if len(track_uris) >= limit:
                    break

            offset += 50  # Increment offset for pagination

    # Randomize the track list to ensure diversity
    track_data = list(zip(edm_tracks, track_uris))
    random.shuffle(track_data)
    edm_tracks, track_uris = zip(*track_data)

    return edm_tracks[:limit], track_uris[:limit]

# Function to update or create a Spotify playlist
def create_or_update_playlist(user_id, playlist_name, track_uris):
    # Search for existing playlist
    playlists = sp.user_playlists(user_id)
    playlist_id = None

    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            playlist_id = playlist['id']
            break

    if playlist_id:
        # Clear the existing playlist
        sp.playlist_replace_items(playlist_id, [])
        print(f"Playlist '{playlist_name}' cleared.")
    else:
        # Create a new playlist if it doesn't exist
        playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
        playlist_id = playlist['id']
        print(f"Playlist '{playlist_name}' created.")

    # Add new tracks to the playlist (in chunks of 100 as required by Spotify API)
    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(playlist_id=playlist_id, items=track_uris[i:i+100])

    print(f"Playlist '{playlist_name}' updated successfully!")

# Main execution for daily updates
def update_playlist_daily():
    try:
        # Get the current user's Spotify ID
        current_user = sp.current_user()
        user_id = current_user['id']

        # Run the playlist update loop
        while True:
            # Fetch random popular EDM songs (up to 10,000)
            print("Fetching random popular EDM songs...")
            edm_songs, edm_uris = get_random_popular_edm_songs(limit=10000)

            # Display the first 10 tracks
            print("Top 10 Random EDM Songs:")
            print("\n".join(edm_songs[:10]))

            # Update the playlist
            create_or_update_playlist(user_id=user_id, playlist_name="Random 10,000 EDM Songs", track_uris=edm_uris)

            # Wait for a day (24 hours)
            print("Waiting for one day before the next update...")
            time.sleep(24 * 60 * 60)  # 1 day in seconds

    except Exception as e:
        print(f"An error occurred: {e}")

# Start the daily update loop
update_playlist_daily()
