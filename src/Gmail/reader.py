

from googleapiclient.errors import HttpError
from client import gmail

# If modifying these scopes, delete the file token.json.


new_auth = gmail("https://www.googleapis.com/auth/gmail.readonly")

def grab_messages_list(service) -> str:

    
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail messages.
    """
    message_list = []

    try:
        # Call the Gmail API
        results = (
            service.users().messages().list(userId="me", labelIds=["INBOX"]).execute()
        )
        messages = results.get("messages", [])
        if not messages:
            print("No messages found.")

        for message in messages:
            msg = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )

            message_list.append(msg["snippet"])
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

    print(message_list)
    return message_list


# Where main action code starts
# =============================

