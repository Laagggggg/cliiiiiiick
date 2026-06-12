// Keyboard + pointer-lock mouse input.
export function createInput(canvas) {
  const keys = new Set();
  let mx = 0, my = 0;
  let pressed = new Set();

  window.addEventListener('keydown', (e) => {
    if (e.repeat) return;
    keys.add(e.code);
    pressed.add(e.code);
  });
  window.addEventListener('keyup', (e) => keys.delete(e.code));
  window.addEventListener('mousemove', (e) => {
    if (document.pointerLockElement === canvas) { mx += e.movementX; my += e.movementY; }
  });

  return {
    keys,
    down: (code) => keys.has(code),
    justPressed: (code) => pressed.has(code),
    endFrame() { pressed.clear(); },
    consumeMouse() { const r = [mx, my]; mx = 0; my = 0; return r; },
    lock() { canvas.requestPointerLock?.(); },
    unlock() { if (document.pointerLockElement) document.exitPointerLock?.(); },
    get locked() { return document.pointerLockElement === canvas; },
  };
}
