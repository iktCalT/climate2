import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const template = await readFile(new URL("../templates/maps.html", import.meta.url), "utf8");
const selectorStart = template.indexOf("function updateSavedMonths()");
const selector = template.slice(selectorStart, template.indexOf("comparisonMonths.querySelectorAll(\".comparison-month-row\").forEach", selectorStart));
const updateSource = selector.slice(0, selector.indexOf("variablePicker.addEventListener"));
const renumberStart = selector.indexOf("function renumberComparisonMonths()");
const renumberAndAdd = selector.slice(renumberStart, selector.indexOf("comparisonMonths.querySelectorAll(\".comparison-month-row\").forEach", renumberStart));
const initializationStart = template.indexOf("comparisonMonths.querySelectorAll(\".comparison-month-row\").forEach", selectorStart);
const initializationEnd = template.indexOf("addComparisonMonth.addEventListener", initializationStart);
const prefilledInitialization = template.slice(initializationStart, initializationEnd);

function element(tag = "div") {
    const listeners = {};
    return {
        tag, children: [], listeners, value: "", disabled: false, textContent: "", focused: 0,
        append(...items) { this.children.push(...items); for (const item of items) item.parent = this; },
        replaceChildren(...items) { this.children = []; this.append(...items); },
        addEventListener(name, callback) { listeners[name] = callback; },
        focus() { this.focused += 1; },
        remove() { this.parent?.children.splice(this.parent.children.indexOf(this), 1); },
        querySelector(selector) {
            return this.children.find(child => child.tag === selector)
                || this.children.map(child => child.querySelector(selector)).find(Boolean)
                || null;
        },
        querySelectorAll(selector) {
            if (selector === ".comparison-month-row") return this.children.filter(child => child.className === selector.slice(1));
            if (selector === "input") return this.children.flatMap(child => child.tag === "input" ? [child] : child.querySelectorAll("input"));
            return [];
        },
    };
}

const comparisonMonths = element();
const addComparisonMonth = element("button");
const document = {createElement: tag => element(tag)};
const maximumMonths = 4;
const prefilledRow = element();
prefilledRow.className = "comparison-month-row";
const prefilledField = element();
const prefilledLabel = element("label");
const prefilledInput = element("input");
prefilledInput.id = "month-picker-1";
prefilledInput.name = "month-picker";
prefilledInput.value = "1960-01";
prefilledField.append(prefilledLabel, prefilledInput);
const prefilledRemove = element("button");
prefilledRow.append(prefilledField, prefilledRemove);
comparisonMonths.append(prefilledRow);
const remainingRow = element();
remainingRow.className = "comparison-month-row";
const remainingField = element();
const remainingLabel = element("label");
const remainingInput = element("input");
remainingInput.id = "month-picker-2";
remainingInput.name = "month-picker";
remainingInput.value = "2000-01";
remainingField.append(remainingLabel, remainingInput);
const remainingRemove = element("button");
remainingRow.append(remainingField, remainingRemove);
comparisonMonths.append(remainingRow);

const makeSelectionFunctions = new Function("comparisonMonths", "addComparisonMonth", "document", "maximumMonths",
    `${renumberAndAdd.replaceAll("{{ start | tojson }}", '"1950-01"').replaceAll("{{ end | tojson }}", '"2026-08"')}\nreturn {renumberComparisonMonths, addMonth};`);
const {renumberComparisonMonths, addMonth} = makeSelectionFunctions(comparisonMonths, addComparisonMonth, document, maximumMonths);
const initializeRows = new Function("comparisonMonths", "addComparisonMonth", "renumberComparisonMonths", prefilledInitialization);
initializeRows(comparisonMonths, addComparisonMonth, renumberComparisonMonths);
assert.equal(prefilledInput.focused, 0, "initializing prefilled selector rows does not move focus");
assert.equal(remainingInput.focused, 0, "initializing prefilled selector rows does not move focus");
assert.equal(addComparisonMonth.disabled, false);
assert.deepEqual(comparisonMonths.children.map(row => row.querySelector("input").value), ["1960-01", "2000-01"]);
assert.deepEqual(comparisonMonths.children.map(row => row.querySelector("label").textContent), ["Compare month 2", "Compare month 3"]);
prefilledRemove.listeners.click();
assert.deepEqual(comparisonMonths.children.map(row => row.querySelector("input").value), ["2000-01"]);
assert.deepEqual(comparisonMonths.children.map(row => row.querySelector("label").textContent), ["Compare month 2"]);
assert.deepEqual(comparisonMonths.children.map(row => row.querySelector("input").id), ["month-picker-1"]);
assert.equal(addComparisonMonth.disabled, false, "removing a prefilled row enables another comparison month");

addMonth("2026-08");
assert.equal(comparisonMonths.children.length, 2);
assert.equal(comparisonMonths.children[1].querySelector("input").value, "2026-08");
assert.equal(comparisonMonths.children[1].querySelector("input").id, "month-picker-2");
assert.equal(comparisonMonths.children[1].querySelector("label").textContent, "Compare month 3");
comparisonMonths.children[1].querySelector("button").listeners.click();
assert.equal(comparisonMonths.children.length, 1);
assert.equal(addComparisonMonth.disabled, false);

addMonth("2001-06");
addMonth("1951-01");
assert.equal(comparisonMonths.children.length, 3);
assert.equal(addComparisonMonth.disabled, true, "three extra rows enforce the four-month cap");
addMonth("1999-01");
assert.equal(comparisonMonths.children.length, 3, "adding beyond the cap has no effect");
comparisonMonths.children[2].querySelector("button").listeners.click();
assert.equal(comparisonMonths.children.length, 2);
assert.deepEqual(comparisonMonths.children.map(row => row.querySelector("input").id), ["month-picker-1", "month-picker-2"]);
assert.deepEqual(comparisonMonths.children.map(row => row.querySelector("label").textContent), ["Compare month 2", "Compare month 3"]);

const savedPicker = element("select");
const variablePicker = element("select");
const useSaved = element("button");
const compareSaved = element("button");
const savedStatus = element("p");
const savedMonths = [
    {month: "1960-01", counts: {temp_mean: 10, precip: 0}},
    {month: "2026-08", counts: {temp_mean: 0, precip: 14}},
];
const suggestions = new Function("savedPicker", "variablePicker", "useSaved", "compareSaved", "savedStatus", "savedMonths", "document",
    `${updateSource}\nreturn updateSavedMonths;`)(savedPicker, variablePicker, useSaved, compareSaved, savedStatus, savedMonths, document);
variablePicker.value = "temp_mean";
suggestions();
const beforeSuggestions = comparisonMonths.querySelectorAll("input").map(input => input.value);
variablePicker.value = "precip";
suggestions();
assert.deepEqual(savedPicker.children.map(option => option.value), ["2026-08"]);
assert.deepEqual(comparisonMonths.querySelectorAll("input").map(input => input.value), beforeSuggestions,
    "changing available-variable suggestions preserves every entered date");
assert.match(savedStatus.textContent, /Your entered dates have not changed/);

console.log("Map selector controls preserve prefilled rows, dates, order and the four-month limit.");
