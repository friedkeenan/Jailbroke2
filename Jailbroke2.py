import praw
import os
import json
import time
import datetime as dt
from DataCollector import DataCollector
from config import *
class Jailbroke(DataCollector):
    body_format='''Removed at {} (UTC)  
Removed by /u/{}

Mod Reply:
***
{}
***
Author: /u/{}  
Created at: {} (UTC)  
[Source]({})  
Score at deletion: {}

Deleted Content:
***
{}
'''
    def __init__(self,post,client_secret,client_id,user_agent,username,password):
        self.username=username
        self.password=password
        DataCollector.__init__(self,client_secret,client_id,user_agent)
        self.post=self.r.subreddit(post)
        self.flair_id=tuple(self.post.flair.link_templates)[0]["id"]
        del self.survived
        del self.del_no_reply
    def run(self):
        last=0
        while self.alive:
            try:
                try:
                    if self.to_check[-1]["created"]>last:
                        with open(self.folder+"/to_check.json","w") as f:
                            stuff=json.dumps(self.to_check,indent=2,sort_keys=True) #Make sure the json looks pretty for my stupid human eyes
                            f.write(stuff)
                        last=self.to_check[-1]["created"]
                except IndexError:
                    pass
                for t in self.deleted:
                    body=Jailbroke.get_body(t)
                    is_sub=True
                    if t["fullname"][1]=="1":
                        title=self.r.comment(t["fullname"][3:]).submission.title
                        is_sub=False
                    else:
                        title=self.r.submission(t["fullname"][3:]).title
                    s=self.post.submit(title,
                                  selftext=body if is_sub else "This post is a container for the removed comment below. It has not been removed.",
                                  flair_id=self.flair_id,
                                  flair_text="Removed" if is_sub else "Not removed")
                    if not is_sub:
                        s.reply(body)
                    print("Posted about "+t["fullname"]+" ("+s.id+")")
                self.deleted=[]
            except Exception as e:
                print(str(e))
                self.r=self.new_reddit()
    def process_data(self):
        while self.alive:
            try:
                for i in self.to_check:
                    if i["fullname"][1]=="1":
                        comment=True
                        t=self.r.comment(i["fullname"][3:])
                        try:
                            t.refresh()
                        except:
                            self.to_check.remove(i)
                            continue
                    else:
                        comment=False
                        t=self.r.submission(i["fullname"][3:])
                    deleted=False
                    try:
                        if comment:
                            replies=t.replies
                        else:
                            replies=t.comments
                    except: #If there was an exception, the object has no replies/comments
                        replies=None
                    if replies:
                        for c in replies:
                            if self.mod_message in c.body and c.distinguished: #If a moderator replies with the standard message when something has been removed
                                temp=i
                                temp["score"]=t.score
                                temp["permalink"]=t.permalink
                                temp["mod_reply"]=DataCollector.organize_data(c)
                                self.deleted.append(temp)
                                deleted=True
                                print("Appended "+i["fullname"]+" to deleted")
                                self.to_check.remove(temp)
                                break
                    if deleted:
                        continue
                    if time.time()-i["accessed"]>=self.wait: #If not enough time has passed to be confident that the comment won't be deleted. It's 6 hours by default
                        self.to_check.remove(i)
            except Exception as e:
                print(str(e))
                self.r=self.new_reddit()
    def new_reddit(self):
        return praw.Reddit(client_secret=self.client_secret,client_id=self.client_id,user_agent=self.user_agent,username=self.username,password=self.password)
    @classmethod
    def get_body(cls,t):
        return cls.body_format.format(dt.datetime.utcfromtimestamp(t["mod_reply"]["created"]).strftime("%Y-%m-%d %H:%M:%S"),
                                    t["mod_reply"]["author"],
                                    t["mod_reply"]["content"],
                                    t["author"],
                                    dt.datetime.utcfromtimestamp(t["created"]).strftime("%Y-%m-%d %H:%M:%S"),
                                    t["permalink"],
                                    t["score"],
                                    t["content"])
if __name__=="__main__":
    if not os.path.exists("Data"):
        os.mkdir("Data")
    jail=Jailbroke("Jailbroke2",rsecret,rid,ua,username,password)
