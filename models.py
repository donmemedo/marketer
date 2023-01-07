from pydantic import BaseModel


class SearchUser(BaseModel):
    username: str


raw_data = {'username': 'daniel'}

my_model = SearchUser(**raw_data)


print(my_model.username)
