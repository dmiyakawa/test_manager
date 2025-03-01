document.addEventListener('DOMContentLoaded', function() {
    const suiteCheckboxes = document.getElementsByClassName('suite-checkbox');
    const caseCheckboxes = document.getElementsByClassName('test-case-checkbox');
    const caseRows = document.getElementsByClassName('test-case-row');
    const startTestRunTop = document.getElementById('start-test-run-top');
    const startTestRunBottom = document.getElementById('start-test-run-bottom');


    // 個別のスイート選択の処理
    for (let checkbox of suiteCheckboxes) {
        checkbox.addEventListener('change', function() {
            updateTestCaseVisibility(this.dataset.suiteId, this.checked);
            
            // スイートが選択された場合、そのスイートのすべてのケースを選択
            const cases = document.querySelectorAll(`.test-case-checkbox[data-suite-id="${this.dataset.suiteId}"]`);
            cases.forEach(caseCheckbox => {
                caseCheckbox.checked = this.checked;
            });
            
            updateStartButtons();
        });
    }

    // 個別のテストケース選択の処理
    for (let checkbox of caseCheckboxes) {
        checkbox.addEventListener('change', updateStartButtons);
    }

    // テストケースの表示/非表示を更新する関数
    function updateTestCaseVisibility(suiteId, show) {
        for (let row of caseRows) {
            if (row.dataset.suiteId === suiteId) {
                row.style.display = show ? '' : 'none';
                if (!show) {
                    const checkbox = row.querySelector('.test-case-checkbox');
                    if (checkbox) checkbox.checked = false;
                }
            }
        }
    }

    // ボタンの有効/無効を更新する関数
    function updateStartButtons() {
        const hasSelectedSuite = Array.from(suiteCheckboxes).some(cb => cb.checked);
        const hasSelectedCase = Array.from(caseCheckboxes).some(cb => cb.checked);
        const enabled = hasSelectedSuite && hasSelectedCase;
        
        startTestRunTop.disabled = !enabled;
        startTestRunBottom.disabled = !enabled;
    }


    // DOMContentLoadedイベントの最後で初期化を実行
    setTimeout(() => {
        // 初期状態ではすべてのスイートとテストケースをチェック

        // スイートをすべて選択
        for (let suite of suiteCheckboxes) {
            suite.checked = true;
            updateTestCaseVisibility(suite.dataset.suiteId, true);
        }

        // テストケースをすべて選択
        for (let testCase of caseCheckboxes) {
            testCase.checked = true;
            testCase.closest('.test-case-row').style.display = '';
        }

        // ボタンの状態を更新
        updateStartButtons();
    }, 100);
});
