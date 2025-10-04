// browser_extension/snap_bridge/block_creator.js - Snap! XML Project Loader

if (typeof window.SnapBlockCreator !== "undefined") {
  console.log("⚠️ SnapBlockCreator already loaded, skipping...");
} else {
  class SnapBlockCreator {
    constructor(apiWrapper) {
      this.apiWrapper = apiWrapper;
    }

    getIDE() {
      return this.apiWrapper.getIDE();
    }

    /**
     * Loads an entire project into the Snap! IDE from an XML string.
     * This is the definitive, "fire-and-forget" version.
     */
    async loadProject(payload) {
      if (!this.apiWrapper.isReady()) {
        throw new Error("Snap! environment is not ready for project import.");
      }

      const { xml, project_name } = payload;
      if (!xml || typeof xml !== "string" || !xml.startsWith("<project")) {
        throw new Error("Invalid or missing XML in 'loadProject' payload.");
      }

      const ide = this.getIDE();
      const finalName = project_name || "Generated Project";

      try {
        // Step 1: Fire the command to load the project.
        ide.openProjectString(xml);
        console.log(`✅ Project load command sent for '${finalName}'.`);

        // Step 2: Immediately return success. We trust Snap!'s importer to handle
        // the rest. The server-side logic should now be responsible for any
        // desired pause before sending subsequent commands.
        return {
          status: "success",
          message: `Project load command for '${finalName}' was successfully sent.`,
        };
      } catch (error) {
        console.error("❌ Error processing 'loadProject' command:", error);
        throw error;
      }
    }
  }

  window.SnapBlockCreator = SnapBlockCreator;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = SnapBlockCreator;
  }
} // End of duplicate loading protection
