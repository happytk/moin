#-*- encoding: utf-8 -*-

# upload허용하는 extensions
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'mp3', 'mp4'])

# 사진 normalize시에 원본파일저장 위치
DATA_DIR = '/volume1/moindev/photo_origins'

# 사진 normalize시에 최대크기
MAX_IMAGE_SIZE = 800, 600

# main화면에서 보여주는 최대 이미지 개수
MAX_IMAGES = 10

MAX_DURATION = 300
KEEP_ALIVE_DELAY = 25
