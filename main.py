from os import getcwd, mkdir
from os.path import join, exists
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup as bs
from selenium.webdriver import Chrome, ChromeOptions

DL = '{}\\downloads\\'.format(getcwd())


# https://stackoverflow.com/questions/45631715/downloading-with-chrome-headless-and-selenium
def enable_download_in_headless_chrome(driver, download_dir):
    # add missing support for chrome "send_command"  to selenium webdriver
    driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    command_result = driver.execute("send_command", params)


class BandScraper(object):
    def __init__(self):
        # url = input("Enter bandcamp album website: ")
        self.url = 'http://musicstore.deru.la/album/1979'
        # self.url = 'https://tonysplendid.bandcamp.com/album/i-know'

        self.soup = self.get_soup()
        self.tracks_to_links = self.get_track_links()

        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        self.driver = Chrome(chrome_options=chrome_options)
        enable_download_in_headless_chrome(self.driver, DL)

        self.get_music()
        self.driver.close()

    def get_soup(self):
        resp = requests.get(self.url).content
        soup = bs(resp, "html.parser")
        return soup

    def get_track_links(self):
        self.album_name = "".join(
            x for x in self.soup.find('h2', attrs={'class': 'trackTitle'}).string.strip().replace(' ', '_')
            if x.isalnum() or x == '_')
        self.album_loc = join(DL, self.album_name)

        if not exists(self.album_loc):
            mkdir(self.album_loc)

        table = self.soup.find('table', attrs={'id': 'track_table'})
        link_tags = table.find_all('a', attrs={'href': True, 'itemprop': True})
        links = [urljoin(self.url, link_tag['href']) for link_tag in link_tags]
        track_names = ["".join(x for x in link_tag.text.replace(' ', '_') if x.isalnum() or x == '_')
                       for link_tag in link_tags]
        links_to_names = {x: y for x, y in zip(links, track_names)}
        return links_to_names

    def get_music(self):

        for link in self.tracks_to_links:
            self.driver.get(link)
            play_button = self.driver.find_element_by_class_name('playbutton')
            play_button.click()
            page_source = self.driver.page_source
            soup = bs(page_source, 'html.parser')
            song_link = soup.find('audio')['src']
            print(song_link)
            self.save_song(link, song_link)

    def save_song(self, track_link, song_link):
        track_loc = join(self.album_loc, self.tracks_to_links[track_link] + '.mp3')
        with open(track_loc, 'wb') as fileobj:
            fileobj.write(requests.get(song_link).content)


def main():
    if not exists(DL):
        mkdir(DL)
    BandScraper()


main()
