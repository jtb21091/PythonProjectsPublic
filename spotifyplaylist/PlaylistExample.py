import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load Spotify API credentials from environment variables
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI") 

if not client_id or not client_secret:
    raise ValueError("Spotify API credentials not found. Please set them as environment variables.")

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope="playlist-modify-public"
))

# Function to fetch top EDM songs
def get_top_edm_songs(limit=30):
    results = sp.search(q="genre:edm", type="track", limit=limit)
    edm_tracks = []
    track_uris = []

    for idx, item in enumerate(results['tracks']['items']):
        track_name = item['name']
        artist_name = item['artists'][0]['name']
        track_uri = item['uri']  # Spotify URI for the track
        edm_tracks.append(f"{idx + 1}. {track_name} by {artist_name}")
        track_uris.append(track_uri)

    return edm_tracks, track_uris

# Function to create a Spotify playlist
def create_playlist(user_id, playlist_name, track_uris):
    # Create a new playlist
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
    sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)
    print(f"Playlist '{playlist_name}' created successfully!")

# Main execution
if __name__ == "__main__":
    try:
        # Fetch top 30 EDM songs and URIs
        edm_songs, edm_uris = get_top_edm_songs()

        # Display the top EDM songs
        print("Top EDM Songs:")
        print("\n".join(edm_songs))

        # Get the current user's Spotify ID
        current_user = sp.current_user()
        user_id = current_user['id']

        # Create a playlist with the top EDM songs
        create_playlist(user_id=user_id, playlist_name="Hottest 30 EDM Songs", track_uris=edm_uris)

    except Exception as e:
        print(f"An error occurred: {e}")
