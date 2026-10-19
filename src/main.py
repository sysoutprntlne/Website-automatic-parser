"""Run from the repository root: python -m src.main --help."""
import argparse
import json
from src.config import Config


def main(argv=None):
    parser = argparse.ArgumentParser(description='Local personalized Gmail reply assistant')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo', help='Synthetic demo; no Gmail, model server or memory required')
    commands.add_parser('auth', help='Explicitly authorize backend Gmail access')
    commands.add_parser('inbox', help='List a small inbox selection')
    imp = commands.add_parser('import-sent', help='Explicit writing-example import')
    imp.add_argument('--limit', type=int, default=100)
    imp.add_argument('--query', default='')
    memory = commands.add_parser('memory')
    memory.add_argument('action', choices=['inspect', 'delete', 'reset'])
    memory.add_argument('--id')
    memory.add_argument('--show-content', action='store_true')
    memory.add_argument('--confirm-reset', action='store_true')
    draft = commands.add_parser('reply', help='Review/edit/regenerate/reject a reply locally')
    draft.add_argument('message_id')
    commands.add_parser('serve', help='Run authenticated loopback backend for extension')
    args = parser.parse_args(argv)
    config = Config.from_env()
    from src.pipeline import Assistant, remember_confirmed
    from src.Model.Llama import Model
    from src.Model.memry.Vector_lib import Memory
    if args.command == 'demo':
        from src.demo import DEMO_EMAIL, DemoModel
        print('SYNTHETIC MOCK DEMO: evaluator approval is simulated; nothing is sent or stored.')
        print(json.dumps(Assistant(DemoModel(), config=config).run(DEMO_EMAIL, 'yeah sure').public(), indent=2))
        return
    if args.command == 'serve':
        from src.backend import serve
        serve(config)
        return
    if args.command == 'memory':
        mem = Memory(config)
        if args.action == 'inspect':
            print(json.dumps(mem.inspect(include_content=args.show_content), indent=2))
        elif args.action == 'delete':
            if not args.id:
                parser.error('memory delete requires --id SOURCE_MESSAGE_ID')
            mem.delete(args.id)
        else:
            mem.reset(confirmed=args.confirm_reset)
        return
    from src.Gmail.client import GmailClient, authenticate
    gmail = GmailClient(authenticate(config, interactive=args.command == 'auth'), config)
    if args.command == 'auth':
        print('Gmail authorization saved privately in the backend.')
    elif args.command == 'inbox':
        for message_id in gmail.messages(limit=10):
            email = gmail.get(message_id)
            print(email.id, email.sender, email.subject)
    elif args.command == 'import-sent':
        print('Imported/upserted:', Memory(config).import_sent(gmail, args.limit, args.query))
    elif args.command == 'reply':
        from src.Gmail.sender import reply_for, send_gmail_msg, approval_digest
        email, memory = gmail.get(args.message_id), Memory(config)
        thread, identity = gmail.thread(email), gmail.identity()
        assistant = Assistant(Model(config), memory, config)
        print(assistant.summarize(email, thread).model_dump_json(indent=2))
        intent = input('Your reply intent: ')
        while True:
            result = assistant.run(email, intent, thread)
            print(json.dumps(result.public(), indent=2))
            if not result.draft or not result.draft.body:
                print('More information is needed; nothing will be sent.')
                return
            body = result.draft.body
            while True:
                action = input('[e]dit / [r]egenerate / re[j]ect / [s]end review: ').lower()
                if action == 'j':
                    return
                if action == 'r':
                    intent = input('Updated reply intent: ')
                    break
                if action == 'e':
                    print('Enter complete edited body. End with a line containing only a dot.')
                    lines = []
                    while (line := input()) != '.':
                        lines.append(line)
                    body = '\n'.join(lines)
                if action == 's':
                    reply = reply_for(email, identity, body)
                    print('FINAL RECIPIENTS, SUBJECT, BODY:')
                    print(reply.model_dump_json(indent=2))
                    if input('Type SEND to approve this exact reply: ') != 'SEND':
                        continue
                    sent_id = send_gmail_msg(gmail, reply, approval_digest(reply))
                    # Delivery and memory persistence are separate outcomes.
                    try:
                        remember_confirmed(gmail, memory, sent_id)
                        print('Confirmed sent and stored in writing memory.')
                    except Exception:
                        print('Send returned success, but memory confirmation failed. Do not resend. Use confirm-sent or import-sent later.')
                    return


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        # Do not print service exception payloads containing private data.
        raise SystemExit(f'Operation failed ({type(error).__name__}). Check configuration or service availability; no automatic send retry.') from None
