#!/usr/bin/env python3

import json
from pathlib import Path
import subprocess

class Config:
  KEY_USEGIT  = "git_enable"
  KEY_REMOTES = "git_remote"
  KEY_BRANCH  = "git_branch"
  KEY_AUTOUPDATE_GIT  = "git_autoupdate"
  KEY_JAR_PATH = "jar_path"

  def __init__(self, config_file = Path("./handler.config"), dir = Path(".")):
    self.dir = dir.absolute()
    self.project_file = self.dir.joinpath("pom.xml")
    self.config_file = config_file.absolute()

    if not self.dir.exists():
      raise Exception("Project directory '{}' does not exist".format(self.dir))      
    if not self.project_file.exists():
      raise Exception("Project file '{}' does not exist".format(self.project_file))
    if not self.config_file.exists():
      self.generate_config(self.config_file)

    with open(str(config_file)) as file:
      self.config = json.load(file)
    
    if self.config[Config.KEY_AUTOUPDATE_GIT]:
      self.update_git()

  def build(self):
    subprocess.run(["mvn", "package"])

  def run(self):
    subprocess.run(["java", "-jar", self.config[Config.KEY_JAR_PATH]])
  
  def update_git(self):
    if not self.config[Config.KEY_USEGIT]:
      return
    
    subprocess.run(["git", "fetch", self.config[Config.KEY_REMOTES]])
    subprocess.run(["git", "reset", self.config[Config.KEY_REMOTES] + "/" + self.config[Config.KEY_BRANCH], "--hard"])
  
  def generate_config(self, config_file):
    use_git = False
    remotes = "origin"
    branch  = "main"
    autoupdate = False
    jar_path = "target/main.jar"
   
    use_git = subprocess.run(["git", "status"], capture_output=True, text=True).stdout != ""
    if use_git:
      branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()

    config = {
      Config.KEY_USEGIT  : use_git,
      Config.KEY_REMOTES : remotes,
      Config.KEY_BRANCH  : branch,
      Config.KEY_AUTOUPDATE_GIT : autoupdate,
      Config.KEY_JAR_PATH : jar_path
    }
    with open(str(config_file), "w") as file:
      json.dump(config, file)

if __name__ == "__main__":
  config = Config()
  config.build()
  config.run()