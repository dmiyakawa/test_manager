document.addEventListener('DOMContentLoaded', function() {
    const caseCheckboxes = document.getElementsByClassName('test-case-checkbox');
    const startTestSessionTop = document.getElementById('start-test-session-top');
    const startTestSessionBottom = document.getElementById('start-test-session-bottom');

    // 個別のテストケース選択の処理
    for (let checkbox of caseCheckboxes) {
        checkbox.addEventListener('change', updateStartButtons);
    }

    // ボタンの有効/無効を更新する関数
    function updateStartButtons() {
        const hasSelectedCase = Array.from(caseCheckboxes).some(cb => cb.checked);
        const enabled = hasSelectedCase;
        
        if (startTestSessionTop) startTestSessionTop.disabled = !enabled;
        if (startTestSessionBottom) startTestSessionBottom.disabled = !enabled;
    }

    // DOMContentLoadedイベントの最後で初期化を実行
    setTimeout(() => {
        // テストケースをすべて選択
        for (let testCase of caseCheckboxes) {
            testCase.checked = true;
        }

        // ボタンの状態を更新
        updateStartButtons();
    }, 100);
});
