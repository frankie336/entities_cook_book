import os
from projectdavid import Entity
from dotenv import load_dotenv

load_dotenv()

Entity()

admin_api_key = os.getenv("ADMIN_API_KEY")

# --- Initialize Client WITH Admin Key ---
# The API endpoint for creating users now requires an authenticated admin user.
admin_client = Entity(base_url="http://localhost:9000", api_key=admin_api_key)

# --- Create a NEW REGULAR User using the Admin Client ---
print("\nAttempting to create a NEW REGULAR user using the Admin API Key...")

try:
    # Define the details for the new REGULAR user
    regular_user_email = "test_regular_user_01@example.com"
    regular_user_full_name = "Regular User One"

    # Use the admin_client to call the create_user endpoint
    # The endpoint logic should verify the admin_client's key belongs to an admin user.
    new_regular_user = admin_client.users.create_user(
        full_name=regular_user_full_name,
        email=regular_user_email,
        # is_admin is NOT set here, so it should default to False per the model
        # oauth_provider='local' # Explicitly set if needed, otherwise service might default
    )

    print("\nNew REGULAR user created successfully by admin:")
    print(new_regular_user)  # new_regular_user will be a Pydantic model (UserRead)
    print(f"User ID: {new_regular_user.id}")

    # --- Next Steps: Generating a Key for the NEW Regular User ---
    print("\n--- Next Steps ---")
    print(
        f"User '{new_regular_user.email}' created, but they do NOT have an API key yet."
    )
    print("To generate a key for this user, you would typically need:")
    print(
        "  1. An API endpoint like POST /users/{user_id}/keys (protected, likely admin-only)"
    )
    print("     - Call this endpoint using the *admin_client* again.")
    print("  2. OR A user-specific flow where the user logs in (e.g., OAuth, password)")
    print("     and generates their own key via an endpoint like POST /me/keys.")

    # Example of CONCEPTUAL admin action to generate key for the new user
    # (Requires a corresponding API endpoint to be implemented)
    # try:
    #    print(f"\nConceptually generating key for user {new_regular_user.id} using admin client...")
    #    # Assuming an endpoint POST /v1/users/{user_id}/keys exists
    #    # and the SDK has a method like admin_client.api_keys.create_user_key(...)
    #    # key_info = admin_client.api_keys.create_user_key(user_id=new_regular_user.id, key_name="Default Key")
    #    # print("Key Info:", key_info) # Response might include plain key or just prefix/metadata
    #    # plain_text_key_for_regular_user = key_info.plain_key # Hypothetical attribute
    # except Exception as key_gen_e:
    #    print(f"Could not generate key (Endpoint/SDK method likely not implemented): {key_gen_e}")


except Exception as e:
    print(f"\nError creating regular user: {e}")
    # If 'e' is an httpx.HTTPStatusError, print more details
    if hasattr(e, "response"):
        print(f"Status Code: {e.response.status_code}")
        try:
            # Try parsing JSON detail, fallback to text
            error_detail = e.response.json()
            print(f"Response Body: {error_detail}")
        except:
            print(f"Response Body: {e.response.text}")
    # raise # Optional: re-raise the exception for full traceback during debugging

print("\nScript finished.")
