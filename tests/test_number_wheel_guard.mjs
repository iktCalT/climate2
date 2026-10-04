import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {test} from "node:test";
import vm from "node:vm";

const source = await readFile(new URL("../static/number_wheel_guard.js", import.meta.url), "utf8");
const layout = await readFile(new URL("../templates/layout.html", import.meta.url), "utf8");

test("shared layout loads the guard", () => {
    assert.match(layout, /<script src="\/static\/number_wheel_guard\.js" defer><\/script>/);
});

test("real delegated wheel handler cancels only numeric-control stepping", () => {
    let listener;
    let options;
    class Element {
        constructor(number = false) { this.number = number; }
        closest(selector) {
            assert.equal(selector, 'input[type="number"]');
            return this.number ? this : null;
        }
    }
    const document = {addEventListener(type, handler, receivedOptions) {
        assert.equal(type, "wheel");
        listener = handler;
        options = receivedOptions;
    }};
    vm.runInNewContext(source, {document, Element});
    assert.equal(options.passive, false);
    assert.equal(options.capture, true);
    function wheel(target, ctrlKey = false) {
        let canceled = false;
        listener({target, ctrlKey, preventDefault() { canceled = true; }});
        return canceled;
    }
    assert.equal(wheel(new Element(true)), true, "dynamically added number input");
    assert.equal(wheel(new Element(true), true), false, "Ctrl-wheel zoom");
    assert.equal(wheel(new Element(false)), false, "other inputs and map wheel");
    assert.equal(wheel({}), false, "non-element target");
    assert.doesNotMatch(source, /\.blur\(|key(?:down|up|press)|stopPropagation|stopImmediatePropagation/);
});
