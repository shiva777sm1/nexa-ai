"""
Rate Limiter - Redis se implement kiya gaya
Author: Shiva
"""

import redis

# Redis se connect ho rahe hain
# host="localhost" - Redis hamare hi computer pe chal raha hai (Docker container ke through)
# port=6379 - Redis ka default port
# decode_responses=True - Redis se jo data aaye, use automatically Python string mein convert karo
#                          (warna bytes format mein aata hai, jo kaam karna mushkil hota hai)
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Rate limit settings
MAX_MESSAGES = 10       # kitne messages allowed hain
TIME_WINDOW_SECONDS = 60  # kitne seconds mein (yahan: 60 seconds mein max 10 messages)


def is_rate_limited(user_id: int) -> bool:
    """
    Check karta hai ki ye user apni limit cross kar chuka hai ya nahi.
    Return: True agar user ne limit cross kar li hai (block karna hai)
            False agar abhi request allowed hai
    """
    # Har user ke liye Redis mein ek UNIQUE key banate hain
    # jaise: "rate_limit:5" (user_id=5 ke liye)
    key = f"rate_limit:{user_id}"

    # Redis se is user ka current count nikalo
    # Agar pehli baar hai (key exist nahi karti), None milega
    current_count = redis_client.get(key)

    if current_count is None:
        # Ye user ka PEHLA message hai is time window mein
        # Counter ko 1 se shuru karo, aur isko 60 seconds baad EXPIRE (delete) hone ke liye set karo
        redis_client.set(key, 1, ex=TIME_WINDOW_SECONDS)
        return False  # Allowed hai

    # Agar current count already limit se zyada ya barabar hai, BLOCK karo
    if int(current_count) >= MAX_MESSAGES:
        return True  # Rate limited - block karo

    # Warna, counter ko 1 se badhao (increment)
    redis_client.incr(key)
    return False  # Abhi allowed hai