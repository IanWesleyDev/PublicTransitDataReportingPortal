$(function() {
    $('#datatable').bootstrapTable({
      striped: true,
      pagination: true,
      showColumns: true,
      showToggle: true,
      showExport: true,
      sortable: true,
      paginationVAlign: 'both',
      pageSize: 25,
      pageList: [10, 25, 50, 100, 'ALL'],
      columns: {{ columns|safe }},
      data: {{ data|safe }},
    });
  });