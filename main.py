from collections import UserDict
import re
from datetime import datetime, timedelta
import pickle


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        self.validate(value)
        super().__init__(value)

    @staticmethod
    def validate(value):
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError(
                "Введіть коректний номер телефону, він повинен містити 10 цифр"
            )


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        for i, phone in enumerate(self.phones):
            if phone.value == old_phone:
                self.phones[i] = Phone(new_phone)
                break

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def days_to_birthday(self):
        if self.birthday:
            today = datetime.today().date()
            next_birthday = self.birthday.value.replace(year=today.year)
            if next_birthday < today:
                next_birthday = self.birthday.value.replace(year=today.year + 1)
            return (next_birthday - today).days
        return None

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        birthday = str(self.birthday) if self.birthday else "Not set"
        return (
            f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"
        )


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        next_week = today + timedelta(days=7)
        first_day_of_next_week = next_week - timedelta(days=next_week.weekday())
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday:
                birthday_this_year = record.birthday.value.replace(
                    year=today.year
                ).date()
                if birthday_this_year < today:
                    birthday_this_year = record.birthday.value.replace(
                        year=today.year + 1
                    ).date()

                if today <= birthday_this_year <= next_week:
                    if birthday_this_year.weekday() <= 4:
                        upcoming_birthdays.append(
                            {
                                "name": record.name.value,
                                "congratulation_date": birthday_this_year.strftime(
                                    "%Y.%m.%d"
                                ),
                            }
                        )
                    elif birthday_this_year.weekday() in {5, 6}:
                        upcoming_birthdays.append(
                            {
                                "name": record.name.value,
                                "congratulation_date": first_day_of_next_week.strftime(
                                    "%Y.%m.%d"
                                ),
                            }
                        )

        return sorted(upcoming_birthdays, key=lambda x: x["congratulation_date"])


# Декоратор для обробки помилок
def input_error(handler):
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except IndexError:
            return "Error: недостатньо аргументів."
        except KeyError:
            return "Error: контакт не знайдено."
        except ValueError as e:
            return f"Error: {e}"

    return wrapper


@input_error
def add_contact(args, book):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def add_birthday(args, book):
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        return "Error: contact not found."
    record.add_birthday(birthday)
    return "Birthday added successfully."


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record is None or not record.birthday:
        return "No birthday information found for this contact."
    return f"{name}'s birthday is on {record.birthday}"


@input_error
def birthdays(args, book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No birthdays in the coming week."
    return "\n".join(
        [
            f"{item['name']}: {item['congratulation_date']}"
            for item in upcoming_birthdays
        ]
    )


def parse_input(user_input):
    parts = user_input.split()
    command = parts[0].lower()
    args = parts[1:]
    return command, args


def main():
    book = load_data()
    # book = AddressBook()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        match command:
            case "close" | "exit":
                print("Good bye!")
                break

            case "hello":
                print("How can I help you?")

            case "add":
                print(add_contact(args, book))

            case "change":
                name, old_phone, new_phone = args
                record = book.find(name)
                if record:
                    record.edit_phone(old_phone, new_phone)
                    print("Phone number updated.")
                else:
                    print("Contact not found.")

            case "phone":
                name = args[0]
                record = book.find(name)
                if record:
                    print(
                        f"{name}'s phones: {', '.join(phone.value for phone in record.phones)}"
                    )
                else:
                    print("Contact not found.")

            case "all":
                for record in book.values():
                    print(record)

            case "add-birthday":
                print(add_birthday(args, book))

            case "show-birthday":
                print(show_birthday(args, book))

            case "birthdays":
                print(birthdays(args, book))

            case _:
                print("Invalid command.")

    save_data(book)

if __name__ == "__main__":
    main()