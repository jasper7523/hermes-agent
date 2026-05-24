"use strict";
/**
 * LM Probe — Language Model API Tester
 *
 * Probes the vscode.lm API to discover what language models
 * are available inside the IDE (Antigravity / VS Code).
 *
 * Three commands:
 *   1. Check Models    — list all registered models
 *   2. Test Generate   — send a simple prompt to the first model
 *   3. Full Report     — dump complete API surface to output channel
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const OUTPUT_CHANNEL_NAME = "LM Probe";
let outputChannel;
// ─── Helpers ────────────────────────────────────────────────────────
function log(msg) {
    const ts = new Date().toISOString().slice(11, 19);
    outputChannel.appendLine(`[${ts}] ${msg}`);
}
function showAndLog(msg, isError = false) {
    log(msg);
    if (isError) {
        vscode.window.showErrorMessage(msg);
    }
    else {
        vscode.window.showInformationMessage(msg);
    }
}
// ─── Command 1: Check Available Models ──────────────────────────────
async function checkModels() {
    log("=== Check Available Models ===");
    // 1. Check if vscode.lm exists at all
    if (!vscode.lm) {
        showAndLog("RESULT: vscode.lm API does NOT exist in this IDE", true);
        return;
    }
    log("vscode.lm API exists: YES");
    // 2. Check if selectChatModels exists
    if (typeof vscode.lm.selectChatModels !== "function") {
        showAndLog("RESULT: vscode.lm.selectChatModels is NOT a function", true);
        return;
    }
    log("vscode.lm.selectChatModels: available");
    // 3. Query all models (no filter)
    try {
        const allModels = await vscode.lm.selectChatModels();
        log(`Total models found: ${allModels.length}`);
        if (allModels.length === 0) {
            showAndLog("RESULT: vscode.lm API exists but 0 models registered");
            return;
        }
        for (const model of allModels) {
            log(`  Model: ${model.name || model.id}`);
            log(`    ID: ${model.id}`);
            log(`    Vendor: ${model.vendor}`);
            log(`    Family: ${model.family}`);
            log(`    Version: ${model.version}`);
            log(`    Max Input Tokens: ${model.maxInputTokens}`);
        }
        const summary = allModels
            .map((m) => `${m.vendor}/${m.family}/${m.name || m.id}`)
            .join(", ");
        showAndLog(`Found ${allModels.length} model(s): ${summary}`);
    }
    catch (err) {
        showAndLog(`Error querying models: ${err.message}`, true);
        log(`Stack: ${err.stack}`);
    }
    // 4. Try specific vendor filters
    for (const vendor of ["google", "copilot", "anthropic", "gemini"]) {
        try {
            const filtered = await vscode.lm.selectChatModels({ vendor });
            if (filtered.length > 0) {
                log(`  Vendor '${vendor}': ${filtered.length} model(s)`);
                for (const m of filtered) {
                    log(`    -> ${m.id} (family=${m.family})`);
                }
            }
        }
        catch {
            // ignore filter errors
        }
    }
    outputChannel.show();
}
// ─── Command 2: Test Generate ───────────────────────────────────────
async function testGenerate() {
    log("=== Test Generate ===");
    if (!vscode.lm || typeof vscode.lm.selectChatModels !== "function") {
        showAndLog("vscode.lm API not available", true);
        return;
    }
    try {
        const models = await vscode.lm.selectChatModels();
        if (models.length === 0) {
            showAndLog("No models available for generation test", true);
            return;
        }
        const model = models[0];
        log(`Using model: ${model.id} (${model.vendor}/${model.family})`);
        const messages = [
            vscode.LanguageModelChatMessage.User("Reply with exactly: HELLO_FROM_LM_PROBE_SUCCESS"),
        ];
        const tokenSource = new vscode.CancellationTokenSource();
        const response = await model.sendRequest(messages, {}, tokenSource.token);
        let fullText = "";
        for await (const chunk of response.text) {
            fullText += chunk;
        }
        log(`Response: ${fullText}`);
        const success = fullText.includes("HELLO_FROM_LM_PROBE_SUCCESS");
        showAndLog(success
            ? `SUCCESS! Model responded correctly via vscode.lm API. Model: ${model.id}`
            : `Model responded but unexpected content: "${fullText.slice(0, 100)}"`);
    }
    catch (err) {
        showAndLog(`Generate failed: ${err.message}`, true);
        log(`Stack: ${err.stack}`);
    }
    outputChannel.show();
}
// ─── Command 3: Full API Report ─────────────────────────────────────
async function fullReport() {
    log("=== Full API Report ===");
    log(`IDE: ${vscode.env.appName}`);
    log(`IDE Version: ${vscode.version}`);
    log(`UI Kind: ${vscode.env.uiKind}`);
    log(`Machine ID: ${vscode.env.machineId?.slice(0, 8)}...`);
    // Check vscode.lm namespace
    log("\n--- vscode.lm namespace ---");
    if (!vscode.lm) {
        log("vscode.lm: UNDEFINED");
    }
    else {
        log("vscode.lm: EXISTS");
        const keys = Object.keys(vscode.lm);
        log(`Properties: ${keys.join(", ") || "(none)"}`);
        for (const key of keys) {
            const val = vscode.lm[key];
            log(`  .${key}: ${typeof val}`);
        }
    }
    // Check relevant APIs
    log("\n--- Other AI-related APIs ---");
    log(`vscode.chat: ${typeof vscode.chat !== "undefined" ? "EXISTS" : "undefined"}`);
    log(`vscode.ai: ${typeof vscode.ai !== "undefined" ? "EXISTS" : "undefined"}`);
    // Check extensions
    log("\n--- Installed AI Extensions ---");
    const aiExtensions = vscode.extensions.all.filter((ext) => ext.id.toLowerCase().includes("gemini") ||
        ext.id.toLowerCase().includes("copilot") ||
        ext.id.toLowerCase().includes("ai") ||
        ext.id.toLowerCase().includes("antigravity") ||
        ext.id.toLowerCase().includes("google"));
    if (aiExtensions.length === 0) {
        log("No AI-related extensions found");
    }
    else {
        for (const ext of aiExtensions) {
            log(`  ${ext.id} v${ext.packageJSON?.version || "?"} (active=${ext.isActive})`);
        }
    }
    // Try model enumeration
    log("\n--- Model Enumeration ---");
    await checkModels();
    showAndLog("Full report written to LM Probe output channel");
    outputChannel.show();
}
// ─── Activation ─────────────────────────────────────────────────────
function activate(context) {
    outputChannel = vscode.window.createOutputChannel(OUTPUT_CHANNEL_NAME);
    log("LM Probe extension activated");
    log(`IDE: ${vscode.env.appName} v${vscode.version}`);
    context.subscriptions.push(vscode.commands.registerCommand("lmProbe.checkModels", checkModels), vscode.commands.registerCommand("lmProbe.testGenerate", testGenerate), vscode.commands.registerCommand("lmProbe.fullReport", fullReport), outputChannel);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map