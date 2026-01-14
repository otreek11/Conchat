"""
Este arquivo importa os schemas do backend.
Para evitar duplicação, importamos diretamente do backend montado no Docker.
"""
import sys
sys.path.append('/backend/src')

from schema import db, User, Group, UserGroup, Friendship, FriendshipStatus, Block
