#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const PLUGIN_DIR = path.join(os.homedir(), '.claude', 'plugins', 'careerops');
const SETTINGS_FILE = path.join(os.homedir(), '.claude', 'settings.json');
const PKG_ROOT = path.join(__dirname, '..');

const PLUGIN_FILES = [
  'skills',
  'scripts',
  'hooks',
  'schemas',
  'agents',
  'templates',
  'config',
  '.claude-plugin',
];

function copyPluginFiles() {
  fs.mkdirSync(PLUGIN_DIR, { recursive: true });
  for (const item of PLUGIN_FILES) {
    const src = path.join(PKG_ROOT, item);
    const dest = path.join(PLUGIN_DIR, item);
    if (!fs.existsSync(src)) continue;
    fs.cpSync(src, dest, { recursive: true, force: true });
  }
}

function updateSettings() {
  let settings = {};
  if (fs.existsSync(SETTINGS_FILE)) {
    try {
      settings = JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf8'));
    } catch (_) {}
  }

  settings.extraKnownMarketplaces = settings.extraKnownMarketplaces || {};
  settings.extraKnownMarketplaces['careerops-local'] = {
    source: { source: 'directory', path: PLUGIN_DIR },
  };
  settings.enabledPlugins = settings.enabledPlugins || {};
  settings.enabledPlugins['careerops@careerops-local'] = true;

  fs.mkdirSync(path.dirname(SETTINGS_FILE), { recursive: true });
  fs.writeFileSync(SETTINGS_FILE, JSON.stringify(settings, null, 2) + '\n');
}

function removeFromSettings() {
  if (!fs.existsSync(SETTINGS_FILE)) return;
  let settings;
  try {
    settings = JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf8'));
  } catch (_) {
    return;
  }
  if (settings.extraKnownMarketplaces) {
    delete settings.extraKnownMarketplaces['careerops-local'];
  }
  if (settings.enabledPlugins) {
    delete settings.enabledPlugins['careerops@careerops-local'];
  }
  fs.writeFileSync(SETTINGS_FILE, JSON.stringify(settings, null, 2) + '\n');
}

function install() {
  console.log('CareerOps — Claude Code Plugin\n');
  console.log(`Installing to: ${PLUGIN_DIR}`);

  copyPluginFiles();
  updateSettings();

  console.log('\n✓ Plugin files installed');
  console.log('✓ Claude Code settings updated');
  console.log('\nRestart Claude Code, then run:');
  console.log('  /careerops:setting-up\n');
  console.log('Requirements:');
  console.log('  • Python 3.10+');
  console.log('  • pip install pyyaml');
  console.log('  • pip install rendercv   (for PDF output)');
}

function uninstall() {
  console.log('Uninstalling CareerOps...\n');

  if (fs.existsSync(PLUGIN_DIR)) {
    fs.rmSync(PLUGIN_DIR, { recursive: true, force: true });
    console.log(`✓ Removed ${PLUGIN_DIR}`);
  } else {
    console.log('Plugin directory not found, nothing to remove.');
  }

  removeFromSettings();
  console.log('✓ Settings updated');
  console.log('\nCareerOps uninstalled. Restart Claude Code to apply.');
}

function update() {
  console.log('Updating CareerOps...\n');
  console.log(`Destination: ${PLUGIN_DIR}`);
  copyPluginFiles();
  console.log('\n✓ Plugin files updated');
  console.log('Restart Claude Code to apply the update.');
}

function help() {
  console.log('Usage: npx careerops [command]\n');
  console.log('Commands:');
  console.log('  install    Install the CareerOps Claude Code plugin (default)');
  console.log('  update     Overwrite installed files with this version');
  console.log('  uninstall  Remove the plugin and clean up settings');
}

const cmd = process.argv[2] || 'install';
switch (cmd) {
  case 'install':   install();   break;
  case 'update':    update();    break;
  case 'uninstall': uninstall(); break;
  case 'help':
  case '--help':
  case '-h':        help();      break;
  default:
    console.error(`Unknown command: ${cmd}`);
    help();
    process.exit(1);
}
