import json, os, re, shutil
from pathlib import Path
from .models import Project, FurnitureItem

NAME=re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,79}$")
class Storage:
    def __init__(self, root=None):
        self.root=Path(root or os.getenv("ROOMLAB_DATA", Path.home()/".roomlab")); self.projects=self.root/"projects"; self.projects.mkdir(parents=True,exist_ok=True)
    def safe(self,name):
        if not NAME.fullmatch(name): raise ValueError("Project names may contain letters, numbers, spaces, '.', '_' and '-'")
        return self.projects/f"{name}.json"
    def list(self): return [json.loads(p.read_text()) for p in sorted(self.projects.glob("*.json"))]
    def get(self,name): return Project.model_validate_json(self.safe(name).read_text())
    def save(self,p): self.safe(p.name).write_text(p.model_dump_json(indent=2)); return p
    def delete(self,name): self.safe(name).unlink(missing_ok=False)
    def rename(self,old,new): self.safe(old).rename(self.safe(new)); p=self.get(new); p.name=new; return self.save(p)
    def duplicate(self,name,new): p=self.get(name); p.name=new; return self.save(p)
    def custom(self):
        p=self.root/"custom_furniture.json"; return json.loads(p.read_text()) if p.exists() else []
    def add_custom(self,item):
        data=self.custom(); data=[x for x in data if x["id"]!=item.id]+[item.model_dump()]; (self.root/"custom_furniture.json").write_text(json.dumps(data,indent=2)); return item

