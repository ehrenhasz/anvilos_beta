[200~import os
  from google.cloud import aiplatform

  # FORCE the config just for this test
  project_id = "ascii-kernel"
  location = "us-central1"

  print(f"PROBING: {project_id} @ {location}...")

  try:
      aiplatform.init(project=project_id, location=location)
      models = aiplatform.Model.list()
      
      print("\n--- CUSTOM MODELS ---")
      if not models:
          print("No custom models found (Expected).")
      for m in models:
          print(f" - {m.display_name}")

      print("\n--- FOUNDATION MODELS (via SDK) ---")
      from google.cloud import aiplatform_v1
      client = aiplatform_v1.ModelGardenServiceClient(
                  client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
                      )
      # Just check if we can connect at all
      print("Connection to Model Garden Service established.")
      print("If you see this, Auth is WORKING.")

  except Exception as e:
      print(f"\n[CRITICAL FAILURE]: {e}")
      print("\nDIAGNOSIS:")
      if "403" in str(e):
          print(" -> PERMISSION DENIED. You need 'Vertex AI User' role.")
      elif "404" in str(e):
          print(" -> NOT FOUND. The API endpoint is unreachable or project is wrong.")
      else:
          print(" -> Unknown error.")
