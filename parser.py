from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import settings
from db import DataBase
from utils import scroll_page


class LoginError(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return 'Возникли проблемы авторизации в Instagram.'


class Parser:
    def __init__(self):
        self.xpath = {
            'profile_link': '//a[contains(@href, "/accounts/activity/")]',
            'login_button': '//a[contains(@href, "/accounts/login/")]',
            'follow_button': '//button[text()="Подписаться"]',
            'links_posts': '//a[contains(@href, "/p/")]',
            'amount_posts': '//span[text()=" публикаций"]',
            'like_button': '//button[@type="button"]//span//*[name()="svg" and @aria-label="Нравится"]',
            'amount_likes': '//a[contains(@href, "/liked_by/")]/span',
            'amount_views': '//span[contains(text(),"Просмотры")]/span',
            'post_date': '//a[contains(@href, "/p/")]/*[name()="time"]',
        }
        self.db = DataBase()
        self.db.create_connection()
        self.db.create_tables()

        options = webdriver.ChromeOptions()
        options.add_argument(f'user-data-dir={settings.full_profile}')  # Path to your chrome profile
        self.browser = webdriver.Chrome(options=options)

    def get_db_data(self) -> list:
        records_db = self.db.get_records('tasks', 'status', 'new')
        return records_db

    def authorize(self, login_url: str) -> None:
        try:
            self.browser.get(login_url)
            name_field = self.browser.find_element_by_xpath('//input[@name="username"]')
            name_field.send_keys(settings.login)
            password_field = self.browser.find_element_by_xpath('//input[@name="password"]')
            password_field.send_keys(settings.password)
            button = self.browser.find_element_by_xpath('//div[text()="Войти"]')
            button.click()
            sleep(5)
        except LoginError as e:
            print(e)

    def run(self, actions):
        while True:
            for task in self.get_db_data():
                print(f'Взял в работу задачу id={task.id} с профилем {task.url}')
                self.db.set_value('tasks', 'status', task.id, 'progress')
                self.browser.get(task.url)
                try:
                    acc = WebDriverWait(self.browser, 3).until(
                        EC.presence_of_element_located((By.XPATH, self.xpath['profile_link']))
                    )
                except TimeoutException:
                    login_button = self.browser.find_element_by_xpath(self.xpath['login_button'])
                    self.authorize(login_button.get_attribute('href'))
                finally:
                    self.run_actions(actions, task)
            sleep(5)

    def run_actions(self, actions: list, task):
        try:
            if 'follow' in actions:
                self.follow()
            if 'like_first_n' in actions:
                result = self.like_posts(int(task.count_posts))
                if result:
                    for post in result:
                        new_post_record = {'task_id': task.id, 'url': post['url'], 'likes': post['likes'],
                                           'create_on': post['date']}
                        self.db.insert_record('posts', new_post_record)
                    self.db.set_value('tasks', 'status', task.id, 'done')
        except Exception as e:
            print('error:', e)
            self.db.set_value('tasks', 'status', task.id, 'error')


    def like_posts(self, n: int = 0):
        try:
            num_all_posts = self.browser.find_element_by_xpath(self.xpath['amount_posts']).text.split(' ')[:-1]
            num_all_posts = ''.join(num_all_posts)
            n = min(int(num_all_posts), n)
            profile_posts = []
            for post in self.get_posts(n):
                self.browser.get(post)

                try:
                    num_likes = WebDriverWait(self.browser, 1).until(
                        EC.presence_of_element_located((By.XPATH, self.xpath['amount_likes']))
                    )
                except TimeoutException:
                    num_likes = self.browser.find_element_by_xpath(self.xpath['amount_views'])

                num_likes = ''.join(num_likes.text.split())
                try:
                    like_button = self.browser.find_element_by_xpath(self.xpath['like_button'])
                    like_button.click()
                except:
                    print('Уже лайкнули')
                finally:
                    post_date = self.browser.find_element_by_xpath(self.xpath['post_date']).get_attribute('title')
                    #print(post, num_likes, post_date)
                    profile_posts.append({'url': post, 'likes': num_likes, 'date': post_date})
            return profile_posts
        except Exception as e:
            print('error', e)
            return False

    def get_posts(self, n: int) -> list:
        posts_on_page = self.browser.find_elements_by_xpath(self.xpath['links_posts'])
        if n <= len(posts_on_page):
            post_list = [post.get_attribute('href') for post in posts_on_page[:n]]
        else:
            post_list = [post.get_attribute('href') for post in posts_on_page]
            while True:
                scroll_page(self.browser)
                posts_on_page = self.browser.find_elements_by_xpath(self.xpath['links_posts'])
                scroll_post_list = [post.get_attribute('href') for post in posts_on_page]
                for post in scroll_post_list:
                    if post not in post_list:
                        post_list.append(post)
                        if len(post_list) == n:
                            break
                break
        return post_list

    def follow(self):
        try:
            button_follow = WebDriverWait(self.browser, 1).until(
                EC.presence_of_element_located((By.XPATH, self.xpath['follow_button']))
            )
            button_follow.click()
            print('Подписался')
        except TimeoutException:
            print('Уже подписан')


if __name__ == '__main__':
    actions = ['follow', 'like_first_n']
    parser = Parser()
    parser.run(actions)
