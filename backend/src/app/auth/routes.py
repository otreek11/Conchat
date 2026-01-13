from flask import Flask, Blueprint, request, jsonify
from validate import *
from schema import *
from logger import logger
from sqlalchemy.exc import IntegrityError


auth_bp = Blueprint("Authorization Blueprint", __name__, url_prefix='/auth')