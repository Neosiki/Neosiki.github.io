if (typeof portfolioProjects !== 'undefined') {
  portfolioProjects.forEach(function (project) {
    if (project.image && /^archive-/.test(project.image) && /\.png(?:\?.*)?$/.test(project.image)) {
      project.image = project.image.replace(/\.png(?:\?.*)?$/, '.svg');
    }
  });
  if (typeof renderProjectArchive === 'function') {
    var active = document.querySelector('.archive-filter.active');
    renderProjectArchive(active ? active.dataset.archiveFilter : 'all');
  }
}
