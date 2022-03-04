run:
	sudo python3 -m pip install pytesseract
	sudo apt update
	sudo apt install tesseract-ocr -y
	sudo python3 ./scraper_wishpo/wishpo.py
