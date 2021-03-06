import shutil
import sys
from os import getcwd, mkdir
from os.path import join, exists
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup as bs
from selenium.webdriver import Chrome, ChromeOptions

DL = '{}\\downloads\\'.format(getcwd())
ZL = '{}\\zips\\'.format(getcwd())


class BandScraper(object):
    def __init__(self, url):
        if not exists(DL):
            mkdir(DL)
        if not exists(ZL):
            mkdir(ZL)
        self.url = url
        self.soup = self.get_soup()
        self.tracks_to_names = self.get_track_links()
        print("Got track names.")
        self.ratio = len(self.tracks_to_names)

        self.get_music()
        print("\nDownload complete.")
        # make zip file

    def make_zip(self):
        shutil.make_archive(join(ZL, self.album_name), 'zip', join(DL, self.album_name))
        return join('zips', self.album_name + '.zip')

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
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--log-level=3')
        self.driver = Chrome(chrome_options=chrome_options)
        print()
        self.update_progress(0)
        for i, link in enumerate(self.tracks_to_names):
            self.driver.get(link)
            play_button = self.driver.find_element_by_class_name('playbutton')
            play_button.click()
            page_source = self.driver.page_source
            soup = bs(page_source, 'html.parser')
            song_link = soup.find('audio')['src']
            self.save_song(link, song_link)
            self.update_progress(i + 1)
        self.driver.quit()

    def save_song(self, track_link, song_link):
        track_loc = join(self.album_loc, self.tracks_to_names[track_link] + '.mp3')
        with open(track_loc, 'wb') as fileobj:
            fileobj.write(requests.get(song_link).content)

    def update_progress(self, progress):
        percentage = min((progress * 100) // self.ratio, 100)
        pounds = u"\u2588" * 3 * (percentage // 10)
        dashes = '   ' * (10 - (percentage // 10))
        print("\r [{0}{1}] {2}%".format(pounds, dashes, percentage), end='')


def main():
    BandScraper(sys.argv[1])


if __name__ == '__main__':
    main()
