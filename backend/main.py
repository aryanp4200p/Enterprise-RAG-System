"""Command line client:  python main.py"""
from app.pipeline import QueryBlockedError, answer_question
from app.security.rbac import UnknownRoleError, list_roles


def main():
    query = input("Enter your query: ")
    role = input(f"Enter role ({'/'.join(list_roles())}): ")

    try:
        result = answer_question(query, role)
    except QueryBlockedError as exc:
        print(f"\n{exc}")
        return
    except UnknownRoleError as exc:
        print(f"\n{exc}. Valid roles: {', '.join(list_roles())}")
        return

    print("\nANSWER:\n")
    print(result["answer"])


if __name__ == "__main__":
    main()
