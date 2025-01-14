from dataclasses import dataclass

@dataclass
class Size:
    """Класс для хранения размеров окна"""
    width: int
    height: int

    @classmethod
    def from_string(cls, size_str: str) -> 'Size':
        """Создает Size из строки формата 'WIDTHxHEIGHT'"""
        width, height = map(int, size_str.split('x'))
        return cls(width, height)

    def __str__(self) -> str:
        """Преобразует Size в строку формата 'WIDTHxHEIGHT'"""
        return f"{self.width}x{self.height}"

    def as_string(self) -> str:
        """Возвращает строковое представление размера в формате WIDTHxHEIGHT"""
        return str(self)
