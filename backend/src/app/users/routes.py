from flask import Flask, Blueprint, request, jsonify
from validate import *
from schema import *
from logger import logger
from sqlalchemy.exc import IntegrityError


users_bp = Blueprint("Users Blueprint", __name__, url_prefix='/user')