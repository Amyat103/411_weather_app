import logging
import os
import time
from typing import Any, List

from weather_app.models.kitchen_model import Meals
from weather_app.utils.logger import configure_logger
from weather_app.utils.random_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


TTL = os.getenv("TTL", 60)  # Default TTL is 60 seconds


class FavoritesModel:
    """
    A class to manage a playlist of songs.

    Attributes:
        current_track_number (int): The current track number being played.
        playlist (List[Song]): The list of songs in the playlist.

    """

    def __init__(self):
        """
        Initializes the PlaylistModel with an empty playlist and the current track set to 1.
        """
        self.current_track_number = 1
        self.playlist: List[Song] = []

    ##################################################
    # Song Management Functions
    ##################################################

    def add_song_to_playlist(self, song: Song) -> None:
        """
        Adds a song to the playlist.

        Args:
            song (Song): the song to add to the playlist.

        Raises:
            TypeError: If the song is not a valid Song instance.
            ValueError: If a song with the same 'id' already exists.
        """
        logger.info("Adding new song to playlist")
        if not isinstance(song, Song):
            logger.error("Song is not a valid song")
            raise TypeError("Song is not a valid song")

        song_id = self.validate_song_id(song.id, check_in_playlist=False)
        if song_id in [song_in_playlist.id for song_in_playlist in self.playlist]:
            logger.error("Song with ID %d already exists in the playlist", song.id)
            raise ValueError(f"Song with ID {song.id} already exists in the playlist")

        self.playlist.append(song)

    def remove_song_by_song_id(self, song_id: int) -> None:
        """
        Removes a song from the playlist by its song ID.

        Args:
            song_id (int): The ID of the song to remove from the playlist.

        Raises:
            ValueError: If the playlist is empty or the song ID is invalid.
        """
        logger.info("Removing song with id %d from playlist", song_id)
        self.check_if_empty()
        song_id = self.validate_song_id(song_id)
        self.playlist = [song_in_playlist for song_in_playlist in self.playlist if song_in_playlist.id != song_id]
        logger.info("Song with id %d has been removed", song_id)

    def remove_song_by_track_number(self, track_number: int) -> None:
        """
        Removes a song from the playlist by its track number (1-indexed).

        Args:
            track_number (int): The track number of the song to remove.

        Raises:
            ValueError: If the playlist is empty or the track number is invalid.
        """
        logger.info("Removing song at track number %d from playlist", track_number)
        self.check_if_empty()
        track_number = self.validate_track_number(track_number)
        playlist_index = track_number - 1
        logger.info("Removing song: %s", self.playlist[playlist_index].title)
        del self.playlist[playlist_index]

    def clear_playlist(self) -> None:
        """
        Clears all songs from the playlist. If the playlist is already empty, logs a warning.
        """
        logger.info("Clearing playlist")
        if self.get_playlist_length() == 0:
            logger.warning("Clearing an empty playlist")
        self.playlist.clear()

    ##################################################
    # Playlist Retrieval Functions
    ##################################################

    def get_all_songs(self) -> List[Song]:
        """
        Returns a list of all songs in the playlist.
        """
        self.check_if_empty()
        logger.info("Getting all songs in the playlist")
        return self.playlist

    def get_song_by_song_id(self, song_id: int) -> Song:
        """
        Retrieves a song from the playlist by its song ID.

        Args:
            song_id (int): The ID of the song to retrieve.

        Raises:
            ValueError: If the playlist is empty or the song is not found.
        """
        self.check_if_empty()
        song_id = self.validate_song_id(song_id)
        logger.info("Getting song with id %d from playlist", song_id)
        return next((song for song in self.playlist if song.id == song_id), None)

    def get_song_by_track_number(self, track_number: int) -> Song:
        """
        Retrieves a song from the playlist by its track number (1-indexed).

        Args:
            track_number (int): The track number of the song to retrieve.

        Raises:
            ValueError: If the playlist is empty or the track number is invalid.
        """
        self.check_if_empty()
        track_number = self.validate_track_number(track_number)
        playlist_index = track_number - 1
        logger.info("Getting song at track number %d from playlist", track_number)
        return self.playlist[playlist_index]

    def get_current_song(self) -> Song:
        """
        Returns the current song being played.
        """
        self.check_if_empty()
        return self.get_song_by_track_number(self.current_track_number)

    def get_playlist_length(self) -> int:
        """
        Returns the number of songs in the playlist.
        """
        return len(self.playlist)
