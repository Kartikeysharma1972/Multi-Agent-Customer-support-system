"""
ChromaDB knowledge base seeder.
Loads 15 FAQ documents for the Technical Agent.
"""

import os
from pathlib import Path

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

FAQ_DOCUMENTS = [
    {
        "id": "faq_001",
        "title": "Getting Started with ProSuite",
        "content": """ProSuite Installation Guide: 
        To install ProSuite, download the installer from your account dashboard at app.prosuite.io/downloads.
        System requirements: Windows 10/11 or macOS 12+, 8GB RAM minimum (16GB recommended), 
        4GB free disk space. Run the installer as administrator on Windows or with sudo on macOS.
        After installation, launch ProSuite and enter your license key found in the welcome email.
        If activation fails, ensure your firewall allows outbound connections on port 443.""",
        "category": "setup"
    },
    {
        "id": "faq_002",
        "title": "Common Error: License Key Invalid",
        "content": """If you receive a 'License Key Invalid' error:
        1. Check for typos — keys are case-sensitive and 32 characters long.
        2. Ensure you're using the correct key for your subscription tier (Basic/Pro/Enterprise).
        3. Verify your subscription is active at account.prosuite.io.
        4. If you recently upgraded, wait 15 minutes for the new key to propagate.
        5. Try deactivating from old devices first (max 2 simultaneous activations on Pro plan).
        6. Contact support with your order confirmation email if the issue persists.""",
        "category": "errors"
    },
    {
        "id": "faq_003",
        "title": "CloudSync Setup and Configuration",
        "content": """CloudSync automatically backs up your data every 6 hours by default.
        To configure: Open Settings > CloudSync > Sync Preferences.
        You can adjust sync frequency (15min/1hr/6hr/daily), choose folders to sync,
        and set bandwidth limits to avoid slowing your connection.
        CloudSync uses AES-256 encryption for all data in transit and at rest.
        Storage limit depends on plan: Basic 50GB, Pro 500GB, Enterprise unlimited.
        To restore files: Settings > CloudSync > Restore > Browse Versions.""",
        "category": "features"
    },
    {
        "id": "faq_004",
        "title": "ProSuite Crashes on Launch",
        "content": """If ProSuite crashes immediately after launching:
        1. Update to the latest version via Help > Check for Updates.
        2. Clear the application cache: delete %APPDATA%\\ProSuite\\Cache on Windows 
           or ~/Library/Caches/ProSuite on macOS.
        3. Run in compatibility mode (Windows only): right-click ProSuite.exe > Properties > Compatibility.
        4. Disable antivirus temporarily to check for interference.
        5. Reinstall the Visual C++ Redistributable (Windows) or update Rosetta 2 (Apple Silicon Mac).
        6. Check crash logs at Help > View Logs and share with support.""",
        "category": "errors"
    },
    {
        "id": "faq_005",
        "title": "DataVault Storage Management",
        "content": """DataVault provides encrypted, redundant cloud storage.
        Features include: version history (last 30 days on Pro), file deduplication,
        end-to-end encryption, and cross-device sync.
        To upgrade storage: Go to Account > Storage > Upgrade.
        Storage quotas reset monthly. Current usage visible in Account > Storage > Usage.
        Files deleted in DataVault are kept in trash for 30 days before permanent deletion.
        To recover deleted files: DataVault > Trash > Select file > Restore.""",
        "category": "features"
    },
    {
        "id": "faq_006",
        "title": "TeamCollab Permission Levels",
        "content": """TeamCollab has four permission levels:
        Owner: Full admin control, billing access, can delete workspace.
        Admin: Manage members, create/delete projects, configure integrations.
        Member: Create and edit content, comment, share within workspace.
        Guest: View-only access to specific projects they're invited to.
        To change permissions: Workspace Settings > Members > Click member > Change Role.
        Enterprise plan supports custom roles with granular permissions.
        SSO (Single Sign-On) available on Enterprise plan via SAML 2.0.""",
        "category": "features"
    },
    {
        "id": "faq_007",
        "title": "Error: Cannot Connect to Server",
        "content": """'Cannot Connect to Server' error troubleshooting:
        1. Check system status at status.prosuite.io for known outages.
        2. Verify your internet connection works for other services.
        3. Flush DNS cache: run 'ipconfig /flushdns' (Windows) or 'dscacheutil -flushcache' (macOS).
        4. Try disabling VPN if active — VPN can block ProSuite connections.
        5. Add prosuite.io to firewall whitelist and ensure ports 443, 8443 are open.
        6. Corporate networks may block connections — contact your IT admin.
        7. Try connecting on mobile data to isolate network vs. application issue.""",
        "category": "errors"
    },
    {
        "id": "faq_008",
        "title": "API Integration Guide",
        "content": """ProSuite REST API allows programmatic access to all features.
        Authentication: Use API keys generated at Account > Developer > API Keys.
        Base URL: https://api.prosuite.io/v2/
        Rate limits: Basic 100 req/min, Pro 1000 req/min, Enterprise unlimited.
        Webhook support: Configure webhooks at Account > Developer > Webhooks.
        All endpoints return JSON. Authentication via Bearer token in Authorization header.
        SDKs available for Python, Node.js, Ruby, PHP, and Go.
        Full API documentation at docs.prosuite.io/api.""",
        "category": "features"
    },
    {
        "id": "faq_009",
        "title": "Password Reset and Account Recovery",
        "content": """To reset your password: Visit login.prosuite.io > Forgot Password > Enter email.
        A reset link valid for 30 minutes will be sent. Check spam/junk if not received.
        If you no longer have access to the account email:
        Contact support with your account email, billing receipt, and government-issued ID.
        Two-factor authentication (2FA) issues: If you've lost your 2FA device,
        use one of your 8 backup codes generated during 2FA setup.
        If backup codes are lost, contact support for account recovery (may take 24-48 hours).""",
        "category": "setup"
    },
    {
        "id": "faq_010",
        "title": "Slow Performance and Optimization",
        "content": """If ProSuite is running slowly:
        1. Ensure your system meets recommended specs (16GB RAM for optimal performance).
        2. Close unnecessary applications running in the background.
        3. Check Task Manager/Activity Monitor — ProSuite should use <5% CPU at idle.
        4. Reduce synced folder size if using CloudSync (large folders slow indexing).
        5. Enable hardware acceleration: Settings > Performance > Use GPU Acceleration.
        6. Disable unused plugins: Settings > Extensions > Disable inactive plugins.
        7. Clear application cache monthly: Help > Maintenance > Clear Cache.""",
        "category": "performance"
    },
    {
        "id": "faq_011",
        "title": "Mobile App Features and Limitations",
        "content": """ProSuite Mobile (iOS & Android) supports:
        - Full CloudSync access and file management
        - TeamCollab messaging and task management  
        - Read-only DataVault access
        - Push notifications for mentions and deadlines
        Limitations vs desktop: No API access, limited offline mode (cached files only),
        no plugin support, no advanced reporting.
        Mobile sync requires WiFi by default (configurable to allow cellular in Settings).
        Minimum OS: iOS 15+, Android 10+. Biometric login supported on both platforms.""",
        "category": "features"
    },
    {
        "id": "faq_012",
        "title": "Export and Data Portability",
        "content": """Exporting your data from ProSuite:
        Full account export: Account > Settings > Privacy > Export My Data.
        Export includes: all files, projects, messages, and account metadata.
        Format: ZIP archive with JSON metadata and original file formats.
        Processing time: Up to 48 hours for large accounts (>100GB).
        Partial export: Select specific projects or date ranges in Export settings.
        API-based export available for Enterprise customers.
        After cancellation: 90-day window to download your data before deletion.""",
        "category": "features"
    },
    {
        "id": "faq_013",
        "title": "Error: File Upload Failed",
        "content": """'File Upload Failed' error causes and solutions:
        1. File size limits: Basic 500MB/file, Pro 5GB/file, Enterprise 50GB/file.
        2. Unsupported formats: .exe, .bat, .scr files are blocked for security.
        3. Filename issues: Remove special characters (/\\:*?\"<>|) from filenames.
        4. Network timeout: For large files, use the desktop app instead of browser.
        5. Storage quota reached: Check available storage in Account > Usage.
        6. Corrupted file: Try re-downloading/re-exporting the source file.
        7. Browser extension conflict: Try uploading in incognito mode.""",
        "category": "errors"
    },
    {
        "id": "faq_014",
        "title": "Enterprise SSO Configuration",
        "content": """Enterprise SSO Setup via SAML 2.0:
        1. Generate SP metadata at Workspace > Security > SSO > Download Metadata.
        2. Configure your IdP (Okta, Azure AD, Google Workspace) with the SP metadata.
        3. Enter IdP metadata URL or upload XML in Workspace > Security > SSO > Configure.
        4. Test with a single user before enforcing SSO for all members.
        5. Enforce SSO: Workspace > Security > SSO > Require SSO for all members.
        JIT (Just-In-Time) provisioning supported: new users created automatically on first login.
        SCIM 2.0 provisioning for automated user lifecycle management.
        Contact enterprise@prosuite.io for white-glove SSO setup assistance.""",
        "category": "setup"
    },
    {
        "id": "faq_015",
        "title": "Backup and Disaster Recovery",
        "content": """ProSuite maintains redundant backups across 3 geographic regions.
        Recovery Point Objective (RPO): 1 hour — data loss limited to max 1 hour.
        Recovery Time Objective (RTO): 4 hours — service restored within 4 hours.
        Version history retention: Basic 7 days, Pro 30 days, Enterprise 1 year.
        To restore a previous version: Right-click file > Version History > Select version.
        Enterprise customers can request specific point-in-time restores by contacting support.
        Annual disaster recovery test reports available to Enterprise customers on request.
        SLA uptime guarantee: 99.9% (Basic/Pro), 99.99% (Enterprise) with credits for downtime.""",
        "category": "features"
    }
]


def seed_knowledge_base():
    """Seed ChromaDB with FAQ documents."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

        # Check if already seeded
        try:
            collection = client.get_collection("technical_kb")
            if collection.count() >= 15:
                print("[+] ChromaDB already seeded")
                return
        except Exception:
            pass

        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        collection = client.get_or_create_collection(
            name="technical_kb",
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        documents = [doc["content"] for doc in FAQ_DOCUMENTS]
        metadatas = [{"title": doc["title"], "category": doc["category"]} for doc in FAQ_DOCUMENTS]
        ids = [doc["id"] for doc in FAQ_DOCUMENTS]

        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"[+] Seeded {len(FAQ_DOCUMENTS)} FAQ documents into ChromaDB")

    except Exception as e:
        print(f"[!] ChromaDB seeding error: {e}")


def query_knowledge_base(query: str, n_results: int = 3) -> list[dict]:
    """Query the technical knowledge base."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        collection = client.get_collection("technical_kb", embedding_function=embedding_fn)

        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count())
        )

        docs = []
        for i, doc in enumerate(results["documents"][0]):
            docs.append({
                "content": doc,
                "title": results["metadatas"][0][i]["title"],
                "category": results["metadatas"][0][i]["category"],
                "relevance_score": 1 - results["distances"][0][i]
            })
        return docs

    except Exception as e:
        print(f"[!] KB query error: {e}")
        return []
