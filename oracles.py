import typing
import random
import json
import os

sources = json.load(open("sources.json", "r"))

class Source:
    def __init__(self, name: str, values: list, finite: bool = False) -> None:
        self.name = name
        self.values = values
        self.total = len(values)
        self.finite = finite
        self.shuffled = False
        self.images = None

    def shuffle(self):
        if self.finite:
            random.shuffle(self.values)
            self.shuffled = True

    def pick(self):
        if not self.finite:
            return random.choice(self.values)
        else:
            return self.values.pop(0)

    def returnValue(self, value):
        if self.finite:
            self.values.append(value)

    def dumpOracle(self):
        spec = {
            "source": self.name,
            "banned_values": [],
            "values": []
        }
        for v in self.values:
            spec["values"].append(
                {"name": v, "id": v, "description": "", "meaning": ""})
        print(json.dumps(spec, indent=4))
        

class SourceBuilder:
    def build(self, spec: dict) -> Source:
        values = []
        for suit in spec.get("suits", []):
            for value in spec.get("values", []):
                values.append(spec["template"].format(suit=suit, value=value))
        values += spec["custom_values"]
        source = Source(spec["name"], values, spec["finite"])
        source.images = spec.get("images")
        return source
    
class Value:
    def __init__(self, oracle, id, state) -> None:
        self.oracle = oracle
        self.id = id
        self.state = state
        self.update()

    def update(self):
        try:
            self.data = next(x for x in self.oracle.spec["values"] if (
                x["name"] == self.id or x["id"] == self.id))
        except Exception as e:
            print(id)
            raise e

    def getName(self) -> str:
        return self.data.get("name", self.data.get("id"))

    def getDesc(self) -> str:
        return self.data["description"]

    def getMeaning(self) -> str:
        if self.state:
            return self.data["meaning_"+self.state]
        return self.data["meaning"]

    def returnValue(self):
        self.oracle.source.returnValue(self.id)
        
    def getImage(self):
        images = ""
        if self.oracle.source.images:
            images = self.oracle.source.images
        if self.oracle.spec.get("images"):
            images = self.oracle.spec.get("images")
        if images:
            images = images.format(name=self.getName(), id=self.id, data=self.data)
        return images
        


class Oracle:
    def __init__(self, source: Source, spec: dict) -> None:
        self.source = source
        self.spec = spec
        self.update()

    def shuffle(self):
        self.source.shuffle()

    def pick(self) -> Value:
        state = None
        if self.spec.get("states"):
            state = random.choice(self.spec["states"])
        return Value(self, self.source.pick(), state)

    def pickN(self, num: int) -> list:
        values = []
        for _ in range(0, num):
            values.append(self.source.pick())
        return values

    def returnValue(self, value):
        self.source.returnValue(value.id)
        
    def pickById(self, id) -> Value:
        if id in self.source.values:
            self.source.values.remove(id)
            state = None
            if self.spec.get("states"):
                state = random.choice(self.spec["states"])
            return Value(self, id, state)
        return None
    
    def getName(self) -> str:
        try:
            return self.spec.get("name", os.path.basename(self.path))
        except:
            return "no name yet"
        
    def getImages(self):
        if "images" in self.spec:
            return self.spec.get("images")
        return self.source.images
    
    def update(self):
        for ban in self.spec["banned_values"]:
            if ban in self.source.values:
                self.source.values.remove(ban)


class OracleBuilder:
    def __init__(self) -> None:
        self.builder = SourceBuilder()

    def build(self, spec: dict) -> Oracle:
        source = self.builder.build(sources[spec["source"]])
        return Oracle(source, spec)
    
    def buildFromFile(self, filename: str) -> Oracle:
        with open(filename, 'r') as f:
            spec = json.load(f)
        oracle = self.build(spec)
        oracle.path = filename
        return oracle
    
    def update(self, oracle: Oracle):
        new_oracle = self.buildFromFile(oracle.path)
        oracle.source.images = new_oracle.source.images
        oracle.spec = new_oracle.spec
        oracle.update()
    
class Record:
    def __init__(self, name: str) -> None:
        self.name = name
        self.values = []
        
    def add(self, value: Value):
        self.values.append(value)

    def discard(self, value: Value):
        self.values.remove(value)

    def returnValue(self, value: Value):
        self.values.remove(value)
        value.returnValue()

    def update(self):
        for value in self.values:
            value.update()

class Workspace:
    def __init__(self, name: str) -> None:
        self.name = name
        self.oracles = []
        self.records = []
        self.builder = OracleBuilder()
        
    def addNewOracle(self, oracle: Oracle) -> None:
        new_oracle = self.builder.build(oracle.spec)
        new_oracle.path = oracle.path
        self.oracles.append(new_oracle)
        
    def addNewRecord(self, name: str):
        self.records.append(Record(name))
        
    def reset(self):
        self.oracles = []
        self.records = []
        
    def update(self):
        for oracle in self.oracles:
            self.builder.update(oracle)
        for record in self.records:
            for value in record.values:
                self.builder.update(value.oracle)
                value.update()

# builder = OracleBuilder()
# builder.builder.build(sources["deck54"]).dumpOracle()
