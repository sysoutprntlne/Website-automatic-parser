from googleapiclient.errors import HttpError
from Gmail.client import gmail


def grab_messages_list() -> tuple[list, list]:
    print("Grabbing message history")

    message_list = []
    contact_list = []
    service, *_ = gmail.gmail_cred_auth()
    try :
        results = (
            service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX"])
            .execute()
        )
        messages = results.get("messages", [])
        if not messages:
            print("No messages found.")
        for message in messages[:6]:

            
            msg = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message["id"],
                    format="metadata",
                    metadataHeaders=["From", "To", "Subject"],
                )
                .execute()
            )
            
            print("executed")
            print(msg.get("snippet"))
            print(msg["payload"]["headers"])

            message_list.append(msg.get("snippet"))
            contact_list.append(msg["payload"]["headers"])


    except HttpError as error:
        print(f"An error occurred: {error}")
    print("sucessful grab")
    return contact_list, message_list