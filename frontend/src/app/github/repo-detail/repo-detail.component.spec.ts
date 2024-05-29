import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RepoDetailComponent } from './repo-detail.component';

describe('RepoDetailComponent', () => {
  let component: RepoDetailComponent;
  let fixture: ComponentFixture<RepoDetailComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [RepoDetailComponent]
    });
    fixture = TestBed.createComponent(RepoDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
