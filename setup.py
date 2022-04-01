from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
  name = 'spotify-ws',         
  packages = ['spotifyws'],   
  version = '0.0.5',      
  license='MIT',        
  description = 'A python wrapper for spotify web sockets',
  long_description=long_description,
  long_description_content_type="text/markdown",
  author = 'Jacopo',
  author_email = 'liljackx0@gmail.com',
  url = 'https://github.com/jacopo-degattis/spotifyws',
  download_url = 'https://github.com/jacopo-degattis/spotifyws/archive/refs/tags/v.0.0.5.tar.gz',
  keywords = ['SPOTIFY', 'WEBSOCKETS', 'MUSIC'], 
  install_requires=[           
          'requests',
          'bs4',
          'pyee',
          'pycookiecheat',
          'pydash',
          'websocket-client',
          'flask',
          'flask-session'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      
    'Intended Audience :: Developers',     
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',  
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
  ],
)
