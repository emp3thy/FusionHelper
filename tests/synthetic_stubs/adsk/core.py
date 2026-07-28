class Application:
    @staticmethod
    def get() -> "Application": ...
    @property
    def activeProduct(self) -> object: ...
    @property
    def measureManager(self) -> object: ...


class ValueInput:
    @staticmethod
    def createByString(s: str) -> "ValueInput": ...
    @staticmethod
    def createByReal(v: float) -> "ValueInput": ...


class Point3D:
    @staticmethod
    def create(x: float, y: float, z: float) -> "Point3D": ...


class Vector3D:
    @staticmethod
    def create(x: float, y: float, z: float) -> "Vector3D": ...


class ObjectCollection:
    @staticmethod
    def create() -> "ObjectCollection": ...
    def add(self, item: object) -> bool: ...
