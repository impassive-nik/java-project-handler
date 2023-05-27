import json
from pathlib import Path
import xml.etree.ElementTree as ET
import subprocess
import re

class Config:
  KEY_USEGIT  = "git_enable"
  KEY_REMOTES = "git_remote"
  KEY_BRANCH  = "git_branch"
  KEY_AUTOUPDATE_GIT  = "git_autoupdate"
  KEY_AUTOBUILD_MAVEN = "maven_autobuild"
  KEY_JAR_PATH = "jar_path"

  def __init__(self, config_file : Path = Path("./handler.config"), project_dir : Path = Path(".")):
    self.dir = project_dir.absolute()
    self.project_file = self.dir.joinpath("pom.xml")
    self.config_file = config_file.absolute()

    if not self.dir.exists():
      raise Exception(f"Project directory '{self.dir}' does not exist")      
    if not self.project_file.exists():
      raise Exception(f"Project file '{self.project_file}' does not exist")
    if not self.config_file.exists():
      self.generate_config(self.config_file)

    with open(str(config_file)) as file:
      self.config = json.load(file)
  
  def is_git_enabled(self):
    return self.config[Config.KEY_USEGIT]
  
  def is_autobuilding(self):
    return self.config[Config.KEY_AUTOBUILD_MAVEN]
  
  def is_autoupdating(self):
    return self.is_git_enabled() and self.config[Config.KEY_AUTOUPDATE_GIT]
  
  def get_git_remote(self):
    return self.config[Config.KEY_REMOTES]
  
  def get_git_branch(self):
    return self.config[Config.KEY_BRANCH]
  
  def get_jar_path(self):
    return self.config[Config.KEY_JAR_PATH]
  
  def generate_config(self, config_file : Path):
    use_git = False
    remotes = "origin"
    branch  = "main"
    autoupdate = False
    autobuild = True

    jar_artifact = "main"
    jar_version  = "1.0"
    try:
      project_xml = ET.parse(self.project_file)
      m = re.match(r'\{.*\}', project_xml.getroot().tag)
      namespace = m.group(0) if m else ''
      for tag in project_xml.findall(f"{namespace}artifactId"):
        jar_artifact = tag.text
      for tag in project_xml.findall(f"{namespace}version"):
        jar_version = tag.text
    except:
      pass
    jar_path = f"target/{jar_artifact}-{jar_version}.jar"
   
    try:
      use_git = subprocess.run(["git", "status"], capture_output=True, text=True, cwd=str(self.dir)).stdout != ""
      if use_git:
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=str(self.dir)).stdout.strip()
    except:
      use_git = False

    config = {
      Config.KEY_USEGIT  : use_git,
      Config.KEY_REMOTES : remotes,
      Config.KEY_BRANCH  : branch,
      Config.KEY_AUTOUPDATE_GIT : autoupdate,
      Config.KEY_AUTOBUILD_MAVEN : autobuild,
      Config.KEY_JAR_PATH : jar_path
    }
    with open(str(config_file), "w") as file:
      json.dump(config, file)

class Handler:
  def __init__(self, config : Config = None):
    if not config:
      config = Config()
    self.config = config

  def update(self):
    if not self.config.is_git_enabled():
      return
    subprocess.run(["git", "fetch", self.config.get_git_remote()], cwd=str(self.config.dir))
    subprocess.run(["git", "checkout", self.config.get_git_remote() + "/" + self.config.get_git_branch()], cwd=str(self.config.dir))

  def build(self, run_tests : bool = False):
    if self.config.is_autoupdating():
      self.update()
    cmd = ["mvn", "package"]
    if not run_tests:
      cmd.append("-DskipTests")
    subprocess.run(cmd)

  def run(self):
    subprocess.run(["java", "-jar", self.config.get_jar_path()])

  def popen(self, merge_stderr : bool = True):
    return subprocess.Popen(["java", "-jar", self.config.get_jar_path()],
                      stdout = subprocess.PIPE,
                      stderr = subprocess.STDOUT if merge_stderr else subprocess.PIPE,
                      stdin = subprocess.PIPE,
                      text = True)