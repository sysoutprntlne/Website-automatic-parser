"""Single-attempt delivery with exact-object approval. Browser uses Gmail send."""
import base64
import hashlib
from email.message import EmailMessage
from src.domain import Reply


class DeliveryUncertain(RuntimeError):
    pass


def reply_for(email, identity, body, reply_all=False):
    identity = identity.lower()
    if email.sent_by_user:
        raise ValueError('Select an incoming message to reply to')
    to = list(dict.fromkeys(a for a in (email.reply_to or [email.sender]) if a != identity))
    cc = []
    if reply_all:
        cc = list(dict.fromkeys(a for a in email.to + email.cc if a != identity and a not in to))
    if not to:
        raise ValueError('No reply recipient available')
    subject = email.subject if email.subject.lower().startswith('re:') else 'Re: ' + email.subject
    refs = ' '.join(dict.fromkeys((email.references + ' ' + email.message_id).split()))
    return Reply(to=to, cc=cc, subject=subject, body=body, thread_id=email.thread_id,
                 in_reply_to=email.message_id, references=refs)


def approval_digest(reply):
    return hashlib.sha256(reply.model_dump_json().encode()).hexdigest()


def send_gmail_msg(client, reply: Reply, approved_digest: str):
    if approved_digest != approval_digest(reply) or not reply.to:
        raise ValueError('Explicit approval must match the final recipients, subject and body')
    msg = EmailMessage()
    msg['From'] = client.identity()
    msg['To'] = ', '.join(reply.to)
    if reply.cc:
        msg['Cc'] = ', '.join(reply.cc)
    msg['Subject'] = reply.subject
    if reply.in_reply_to:
        msg['In-Reply-To'] = reply.in_reply_to
    if reply.references:
        msg['References'] = reply.references
    msg.set_content(reply.body)
    request = {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}
    if reply.thread_id:
        request['threadId'] = reply.thread_id
    try:
        # Never retry: the remote service may have delivered before a timeout.
        result = client.service.users().messages().send(userId='me', body=request).execute(num_retries=0)
        if not result.get('id'):
            raise ValueError('Missing sent message ID')
    except Exception:
        raise DeliveryUncertain('Send outcome unknown. Check Gmail Sent before any further action.') from None
    return result['id']
