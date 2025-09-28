package com.optionalgo.repository;

import com.optionalgo.model.SampleModel;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SampleModelRepository extends JpaRepository<SampleModel, Long> {
}
