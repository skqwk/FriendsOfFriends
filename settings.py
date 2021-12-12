
with open("token.txt", encoding='utf8') as file:
    TOKEN_AND_VERSION = file.readline()
    
requestToGetFriends = "https://api.vk.com/method/friends.get?user_id"
requestToGetDataOfUser = "https://api.vk.com/method/users.get?user_ids"
getMultiple = "https://api.vk.com/method/execute?code=return ["
fieldsForFriends = "&fields=name,sex,bdate,education,city"



