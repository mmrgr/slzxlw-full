(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var accent3 = style.getPropertyValue('--accent3').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  // --- Chart 1: Methods Distribution (图2) ---
  var chart1El = document.getElementById('chart-methods');
  if (chart1El) {
    var chart1 = echarts.init(chart1El, null, { renderer: 'svg' });
    chart1.setOption({
      animation: false,
      tooltip: {
        trigger: 'item',
        appendToBody: true,
        formatter: '{b}: {c}篇 ({d}%)'
      },
      legend: {
        orient: 'horizontal',
        bottom: 10,
        textStyle: { color: muted, fontSize: 12 }
      },
      series: [{
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: bg2,
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{c}篇',
          color: ink,
          fontSize: 12,
          fontWeight: 600
        },
        labelLine: { length: 15, length2: 10 },
        data: [
          { value: 4, name: 'UWM框架与案例', itemStyle: { color: accent } },
          { value: 2, name: '生态网络分析(ENA)', itemStyle: { color: accent2 } },
          { value: 2, name: '纽带方法(Nexus)', itemStyle: { color: accent3 } },
          { value: 3, name: '建模工具与新兴主题', itemStyle: { color: '#6c5ce7' } }
        ]
      }]
    });
    window.addEventListener('resize', function() { chart1.resize(); });
  }

  // --- Chart 2: Research Gaps Assessment Matrix (图3) ---
  var chart2El = document.getElementById('chart-gaps');
  if (chart2El) {
    var chart2 = echarts.init(chart2El, null, { renderer: 'svg' });
    chart2.setOption({
      animation: false,
      tooltip: {
        trigger: 'item',
        appendToBody: true,
        formatter: function(p) {
          return '<b>' + p.data[3] + '</b><br/>科学价值: ' + p.data[0] + '/5<br/>可行性: ' + p.data[1] + '/5<br/>优先级: ' + p.data[4];
        }
      },
      grid: {
        left: 60,
        right: 30,
        top: 50,
        bottom: 60
      },
      xAxis: {
        name: '可行性 (资源可得性 × 操作难度)',
        nameLocation: 'middle',
        nameGap: 35,
        nameTextStyle: { color: muted, fontSize: 13, fontWeight: 600 },
        min: 0,
        max: 6,
        interval: 1,
        axisLine: { lineStyle: { color: rule } },
        axisLabel: { color: muted },
        splitLine: { lineStyle: { color: rule, type: 'dashed', opacity: 0.5 } }
      },
      yAxis: {
        name: '科学价值 (Nature子刊潜力)',
        nameLocation: 'middle',
        nameGap: 40,
        nameTextStyle: { color: muted, fontSize: 13, fontWeight: 600 },
        min: 0,
        max: 6,
        interval: 1,
        axisLine: { lineStyle: { color: rule } },
        axisLabel: { color: muted },
        splitLine: { lineStyle: { color: rule, type: 'dashed', opacity: 0.5 } }
      },
      series: [{
        type: 'scatter',
        symbolSize: function(data) {
          return data[2];
        },
        data: [
          // [可行性, 科学价值, 气泡大小, 名称, 优先级]
          [5, 5, 45, '空白一: ENA-动态模拟耦合', '最高'],
          [4, 3.5, 30, '空白二: 时空精度提升', '中'],
          [3.5, 4, 32, '空白三: 跨系统耦合', '中高'],
          [3, 3.5, 25, '空白四: 社会经济维度', '中'],
          [2.5, 4.5, 28, '空白五: AI基础设施水足迹', '高但难']
        ],
        itemStyle: {
          color: function(params) {
            var colors = [accent, accent2, accent3, '#6c5ce7', '#f4a261'];
            return colors[params.dataIndex];
          },
          opacity: 0.75,
          shadowBlur: 10,
          shadowColor: 'rgba(0,0,0,0.1)'
        },
        label: {
          show: true,
          formatter: function(p) {
            return p.data[3].split(':')[0];
          },
          position: 'top',
          color: ink,
          fontSize: 11,
          fontWeight: 600,
          distance: 8
        },
        markArea: {
          silent: true,
          itemStyle: { color: accent, opacity: 0.04 },
          data: [[
            { xAxis: 4, yAxis: 6 },
            { xAxis: 6, yAxis: 4 }
          ]]
        },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: rule, type: 'dashed' },
          data: [
            { xAxis: 4, label: { show: false } }
          ]
        }
      }]
    });
    window.addEventListener('resize', function() { chart2.resize(); });
  }
})();
