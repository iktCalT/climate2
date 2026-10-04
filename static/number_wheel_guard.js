// Suppress wheel stepping only while the pointer is over a numeric input.
document.addEventListener("wheel", (event) => {
    const target = event.target;
    if (!event.ctrlKey && target instanceof Element && target.closest('input[type="number"]')) {
        event.preventDefault();
    }
}, { passive: false, capture: true });
